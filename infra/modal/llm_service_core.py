"""Shared vLLM GPU service implementation for prod and playground Modal apps (ADR-037)."""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from infra.modal.llm_app import ServeRole


class LlmServiceCore:
    """Undecorated GPU inference core — subclass adds ``@modal.enter/method`` hooks."""

    serve_role: ClassVar[ServeRole]
    allow_model_reload: ClassVar[bool]

    _llm: object | None
    _loaded_model_arg: str | None
    _loaded_cache_key: tuple[str, str | None] | None
    _lora_request: object | None

    def load_model(self) -> None:
        """Lazy-load vLLM on first request (supports default + playground tag switches)."""
        self._llm = None
        self._loaded_model_arg = None
        self._loaded_cache_key = None
        self._lora_request = None
        self._snapshot_mode = False
        self._adapter_id = None
        self._adapter_hash = None

    def unload_model(self) -> None:
        from infra.modal.llm_app import _shutdown_vllm_engine

        _shutdown_vllm_engine(getattr(self, "_llm", None))
        self._llm = None
        self._loaded_model_arg = None
        self._loaded_cache_key = None
        self._lora_request = None
        self._snapshot_mode = False
        self._adapter_id = None
        self._adapter_hash = None

    def _snapshot_enter_build(self) -> None:
        """``snap=True``: load pinned base (+ LoRA capacity), warm, Level-1 sleep (ADR-022)."""
        from infra.modal.llm_app import (
            MODEL_ID,
            _llm_engine_kwargs,
            max_model_len_for,
        )
        from vecinita_shared_schemas.finetune import DEFAULT_LORA_MAX_RANK
        from vllm import LLM, SamplingParams

        self._llm = None
        self._loaded_model_arg = None
        self._loaded_cache_key = None
        self._lora_request = None
        # enable_lora without a pinned adapter so restore can bind promote without rebuild.
        engine_kwargs = dict(
            _llm_engine_kwargs(max_model_len=max_model_len_for(MODEL_ID), model=MODEL_ID)
        )
        engine_kwargs["enable_lora"] = True
        engine_kwargs["max_loras"] = 1
        engine_kwargs["max_lora_rank"] = DEFAULT_LORA_MAX_RANK
        self._llm = LLM(**engine_kwargs)
        self._loaded_model_arg = MODEL_ID
        params = SamplingParams(max_tokens=1)
        # Tiny + RAG-sized warmups move JIT/graph work into snapshot creation.
        _ = self._llm.generate(["warmup"], params)
        rag_ish = "Context:\n" + ("x " * 400) + "\nQuestion: what is this?\nAnswer:"
        _ = self._llm.generate([rag_ish], params)
        sleep = getattr(self._llm, "sleep", None)
        if not callable(sleep):
            msg = "vLLM Level-1 sleep is required for GPU memory snapshot capture"
            raise TypeError(msg)
        _ = sleep(level=1)
        self._snapshot_mode = True

    def _snapshot_enter_restore(self) -> None:
        """``snap=False``: wake engine and bind current promoted LoRA (#316)."""
        llm = getattr(self, "_llm", None)
        if llm is None:
            msg = "snapshot restore expected a restored vLLM engine before wake_up"
            raise RuntimeError(msg)
        wake = getattr(llm, "wake_up", None)
        if not callable(wake):
            msg = "vLLM wake_up is required for GPU memory snapshot restore"
            raise TypeError(msg)
        _ = wake()
        self._bind_lora_after_restore()
        self._snapshot_mode = True

    def _bind_lora_after_restore(self) -> None:
        """Resolve promoted adapter after snapshot restore (Volume mutate ≠ snap invalidate).

        Default ``VECINITA_LLM_LORA_RESOLVE=post_restore``: bind from volume and verify
        SHA-256 (``VECINITA_FINETUNE_ADAPTER_HASH``) with constant-time compare (EV-316).
        ``snapshot_bound`` skips integrity verify (legacy/debug only).
        """
        from infra.modal.llm_app import (
            MODEL_ID,
            _adapter_load_for_role,
            _build_lora_request,
        )
        from vecinita_shared_schemas.finetune import (
            parse_lora_resolve_mode,
            require_post_restore_adapter_hash,
            verify_adapter_integrity,
        )

        adapter_id, adapter_dir = _adapter_load_for_role(self.serve_role)
        if adapter_id is not None and adapter_dir is not None and not Path(adapter_dir).is_dir():
            msg = f"promoted LoRA adapter missing on volume: {adapter_id} ({adapter_dir})"
            raise RuntimeError(msg)

        mode = parse_lora_resolve_mode()
        if mode == "post_restore" and adapter_id is not None:
            expected = require_post_restore_adapter_hash(adapter_id=adapter_id)
            if adapter_dir is None or expected is None:
                msg = f"promoted LoRA adapter dir/hash unresolved for {adapter_id}"
                raise RuntimeError(msg)
            _ = verify_adapter_integrity(adapter_dir=adapter_dir, expected_hash=expected)
            self._adapter_hash = expected
        else:
            self._adapter_hash = None

        self._lora_request = _build_lora_request(adapter_id, adapter_dir)
        self._loaded_model_arg = MODEL_ID
        self._loaded_cache_key = (MODEL_ID, adapter_id)
        self._adapter_id = adapter_id

    def _ensure_model_loaded(self, model_id: str | None) -> None:
        from infra.modal.llm_app import (
            _adapter_load_for_role,
            _build_lora_request,
            _llm_engine_kwargs,
            _resolve_vllm_model_arg,
            _shutdown_vllm_engine,
            max_model_len_for,
        )
        from vecinita_shared_schemas.finetune import merge_lora_engine_kwargs
        from vllm import LLM, SamplingParams

        if getattr(self, "_snapshot_mode", False) and self._llm is not None:
            # Refresh LoRA pin without rebuilding the snapped base engine.
            adapter_id, adapter_dir = _adapter_load_for_role(self.serve_role)
            cache_key = (
                _resolve_vllm_model_arg(
                    None,
                    allow_model_reload=self.allow_model_reload,
                ),
                adapter_id,
            )
            if getattr(self, "_loaded_cache_key", None) != cache_key:
                if (
                    adapter_id is not None
                    and adapter_dir is not None
                    and not Path(adapter_dir).is_dir()
                ):
                    msg = f"promoted LoRA adapter missing on volume: {adapter_id} ({adapter_dir})"
                    raise RuntimeError(msg)
                self._lora_request = _build_lora_request(adapter_id, adapter_dir)
                self._loaded_cache_key = cache_key
            return

        if not self.allow_model_reload:
            model_id = None
        resolved = _resolve_vllm_model_arg(
            model_id,
            allow_model_reload=self.allow_model_reload,
        )
        adapter_id, adapter_dir = _adapter_load_for_role(self.serve_role)
        cache_key = (resolved, adapter_id)
        if getattr(self, "_loaded_cache_key", None) == cache_key and self._llm is not None:
            return
        _shutdown_vllm_engine(getattr(self, "_llm", None))
        self._llm = None
        self._loaded_model_arg = None
        self._loaded_cache_key = None
        self._lora_request = None
        import gc

        _ = gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except Exception:
            pass
        engine_kwargs = merge_lora_engine_kwargs(
            _llm_engine_kwargs(max_model_len=max_model_len_for(resolved), model=resolved),
            adapter_dir=adapter_dir,
        )
        self._llm = LLM(**engine_kwargs)
        self._lora_request = _build_lora_request(adapter_id, adapter_dir)
        self._loaded_model_arg = resolved
        self._loaded_cache_key = cache_key
        warmup_kwargs: dict[str, object] = {}
        if self._lora_request is not None:
            warmup_kwargs["lora_request"] = self._lora_request
        self._llm.generate(["warmup"], SamplingParams(max_tokens=1), **warmup_kwargs)

    def _generate_text(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str:
        from vllm import SamplingParams

        self._ensure_model_loaded(model_id)
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=1.15,
        )
        if self._llm is None:
            msg = "LlmService model is not loaded"
            raise RuntimeError(msg)
        gen_kwargs: dict[str, object] = {}
        lora = getattr(self, "_lora_request", None)
        if lora is not None:
            gen_kwargs["lora_request"] = lora
        generate = self._llm.generate
        outputs = generate([prompt], params, **gen_kwargs)
        return outputs[0].outputs[0].text

    def _stream_text_deltas(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> Iterator[str]:
        """Yield incremental token text from the vLLM engine (RD-164 / TP-S010-22)."""
        from vllm import SamplingParams

        self._ensure_model_loaded(model_id)
        if self._llm is None:
            msg = "LlmService model is not loaded"
            raise RuntimeError(msg)
        engine = getattr(self._llm, "llm_engine", None)
        if engine is None or not hasattr(engine, "add_request") or not hasattr(engine, "step"):
            msg = "vLLM llm_engine streaming API unavailable"
            raise RuntimeError(msg)
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=1.15,
        )
        request_id = f"stream-{uuid.uuid4()}"
        lora = getattr(self, "_lora_request", None)
        if lora is not None:
            engine.add_request(request_id, prompt, params, lora_request=lora)
        else:
            engine.add_request(request_id, prompt, params)
        previous = ""
        while engine.has_unfinished_requests():
            for request_output in engine.step():
                if getattr(request_output, "request_id", None) != request_id:
                    continue
                outputs = getattr(request_output, "outputs", None) or []
                if not outputs:
                    continue
                text = getattr(outputs[0], "text", "") or ""
                delta = text[len(previous) :]
                previous = text
                if delta:
                    yield delta
                if getattr(request_output, "finished", False):
                    return

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> str:
        return self._generate_text(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id,
        )

    def stream_tokens(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        model_id: str | None = None,
    ) -> Iterator[str]:
        """Yield incremental tokens for SSE (real vLLM deltas — RD-164)."""
        yield from self._stream_text_deltas(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_id=model_id,
        )

    def warm_model(self, model_id: str | None = None) -> str:
        """Preload a model into VRAM (fold cold-start into warm-up window)."""
        from infra.modal.llm_app import _resolve_vllm_model_arg

        self._ensure_model_loaded(model_id)
        return _resolve_vllm_model_arg(
            model_id,
            allow_model_reload=self.allow_model_reload,
        )
