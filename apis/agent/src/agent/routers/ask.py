"""Question-answering endpoints for deterministic and streaming agent responses."""

import asyncio
from typing import Literal

from fastapi import APIRouter

from src.agent.openapi_examples import (
    AGENT_ASK_CLARIFICATION_RESPONSE,
    AGENT_ASK_CONTEXT_ANSWER,
    AGENT_ASK_FLAG_FALSE,
    AGENT_ASK_FLAG_TRUE,
    AGENT_ASK_LANG,
    AGENT_ASK_MODEL,
    AGENT_ASK_PROVIDER,
    AGENT_ASK_QUERY_ALIAS,
    AGENT_ASK_QUESTION,
    AGENT_ASK_RERANK_TOP_K,
    AGENT_ASK_TAG_MATCH_MODE,
    AGENT_ASK_TAGS,
    AGENT_ASK_THREAD_ID,
)

from .. import main as agent_main

router = APIRouter()


@router.get("/ask")
async def ask_question(
    question: str | None = agent_main.Query(
        default=None,
        description="Primary question text (use ``query`` only as a legacy alias).",
        openapi_examples=AGENT_ASK_QUESTION,
    ),
    query: str | None = agent_main.Query(
        default=None,
        description="Legacy alias for ``question`` when ``question`` is omitted.",
        openapi_examples=AGENT_ASK_QUERY_ALIAS,
    ),
    thread_id: str = agent_main.Query(
        default="default",
        description="Conversation thread id for correlating follow-ups.",
        openapi_examples=AGENT_ASK_THREAD_ID,
    ),
    lang: str | None = agent_main.Query(
        default=None,
        description="Force language (e.g. en, es) instead of auto-detection.",
        openapi_examples=AGENT_ASK_LANG,
    ),
    provider: str | None = agent_main.Query(
        default=None,
        description="LLM provider override (ollama-compatible stack).",
        openapi_examples=AGENT_ASK_PROVIDER,
    ),
    model: str | None = agent_main.Query(
        default=None,
        description="Model id override; must exist in ``GET /config`` when set.",
        openapi_examples=AGENT_ASK_MODEL,
    ),
    context_answer: str | None = agent_main.Query(
        default=None,
        description="Prior assistant answer for short contextual follow-ups.",
        openapi_examples=AGENT_ASK_CONTEXT_ANSWER,
    ),
    tags: str | None = agent_main.Query(
        default=None,
        description="Comma-separated metadata tags for retrieval filtering.",
        openapi_examples=AGENT_ASK_TAGS,
    ),
    tag_match_mode: Literal["any", "all"] = agent_main.Query(
        default="any",
        description="Tag match mode: any|all",
        openapi_examples=AGENT_ASK_TAG_MATCH_MODE,
    ),
    include_untagged_fallback: bool = agent_main.Query(
        default=True,
        description="When tag filter is active, include untagged documents as fallback.",
        openapi_examples=AGENT_ASK_FLAG_TRUE,
    ),
    rerank: bool = agent_main.Query(
        default=False,
        description="Enable reranking of retrieved chunks.",
        openapi_examples=AGENT_ASK_FLAG_FALSE,
    ),
    rerank_top_k: int = agent_main.Query(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retain after reranking.",
        openapi_examples=AGENT_ASK_RERANK_TOP_K,
    ),
):
    """Handle non-streaming Q&A requests using intent-gated deterministic RAG."""
    started_at = agent_main.time.perf_counter()

    question, query, lang, provider, model, tags, context_answer = (
        agent_main._coerce_ask_query_parameters(
            question=question,
            query=query,
            lang=lang,
            provider=provider,
            model=model,
            tags=tags,
            context_answer=context_answer,
        )
    )

    if question is None and query is not None:
        question = query
    if not question:
        raise agent_main.HTTPException(
            status_code=400,
            detail="Question parameter cannot be empty. Use 'question' or 'query'.",
        )

    try:
        provider, model = agent_main._resolve_effective_provider_model(provider, model)

        if not lang:
            lang = agent_main.detect_ask_query_language(question)

        from src.agent.guardrails_config import validate_input, validate_output

        contextual_follow_up = bool(context_answer) and agent_main._is_contextual_follow_up(
            question, lang
        )
        guard_result = validate_input(
            question,
            lang=lang,
            allow_contextual_follow_up=contextual_follow_up,
        )
        if not guard_result.passed:
            return agent_main._response_payload(
                guard_result.reason,
                thread_id=thread_id,
                started_at=started_at,
                sources=[],
            )
        effective_question = guard_result.redacted if guard_result.redacted else question

        if agent_main._is_non_linguistic_question(effective_question):
            return agent_main._response_payload(
                agent_main._non_linguistic_query_reply(lang),
                thread_id=thread_id,
                started_at=started_at,
                sources=[],
            )

        if contextual_follow_up:
            llm_started_at = agent_main.time.perf_counter()
            answer = await asyncio.to_thread(
                agent_main._build_contextual_follow_up_answer,
                question=effective_question,
                prior_answer=context_answer or "",
                language=lang,
                provider=provider,
                model=model,
            )
            llm_ms = int((agent_main.time.perf_counter() - llm_started_at) * 1000)

            out_guard = validate_output(answer)
            if not out_guard.passed:
                answer = out_guard.reason
            elif out_guard.redacted:
                answer = out_guard.redacted

            return agent_main._response_payload(
                answer,
                thread_id=thread_id,
                started_at=started_at,
                sources=[],
                latency_breakdown={"retrieval_invoke_ms": 0, "llm_ms": llm_ms, "db_search": {}},
            )

        agent_main.logger.info(
            "\n--- New request received: '%s' (Detected Language: %s, Thread: %s) ---",
            effective_question,
            lang,
            thread_id,
        )

        answer_seeking = agent_main._is_answer_seeking_query(effective_question, lang)
        if not answer_seeking:
            local_static = agent_main._find_static_faq_answer(effective_question, lang)
            if local_static:
                agent_main.logger.info(
                    "Returning static FAQ answer (local matcher, non-answer intent)."
                )
                return agent_main._response_payload(
                    local_static,
                    thread_id=thread_id,
                    started_at=started_at,
                )
            try:
                static_answer = agent_main.static_response_tool.invoke(
                    {"query": effective_question, "language": lang}
                )
                if static_answer:
                    agent_main.logger.info(
                        "Returning static FAQ answer without retrieval (non-answer intent)."
                    )
                    return agent_main._response_payload(
                        static_answer,
                        thread_id=thread_id,
                        started_at=started_at,
                    )
            except Exception as static_exc:
                agent_main.logger.warning("Static response check failed: %s", static_exc)

        request_tags = agent_main.parse_tags_input(tags)
        search_token = agent_main.set_db_search_options(
            tags=request_tags,
            tag_match_mode=tag_match_mode,
            include_untagged_fallback=include_untagged_fallback,
            rerank=rerank,
            rerank_top_k=rerank_top_k,
        )
        try:
            agent_main.logger.info("Intent gate: answer_seeking=%s", answer_seeking)
            retrieval_ms = 0
            llm_ms = 0

            if not answer_seeking:
                static_faq_answer = agent_main._find_static_faq_answer(effective_question, lang)
                if static_faq_answer:
                    answer = static_faq_answer
                else:
                    answer, llm_ms = await asyncio.to_thread(
                        agent_main._non_answer_brief_llm_reply,
                        provider=provider,
                        model=model,
                        lang=lang,
                        effective_question=effective_question,
                    )
                sources: list[dict] = []
            else:
                agent_main.logger.info(
                    "Running mandatory one-shot db_search for answer-seeking query"
                )
                retrieval_started_at = agent_main.time.perf_counter()
                raw_search = await asyncio.to_thread(
                    agent_main.db_search_tool.invoke, effective_question
                )
                retrieval_ms = int((agent_main.time.perf_counter() - retrieval_started_at) * 1000)
                retrieved_docs = agent_main._parse_db_search_docs(
                    raw_search if isinstance(raw_search, str) else str(raw_search)
                )
                weak_retrieval = agent_main._is_weak_retrieval(retrieved_docs)

                llm_started_at = agent_main.time.perf_counter()
                answer = await asyncio.to_thread(
                    agent_main._build_deterministic_rag_answer,
                    question=effective_question,
                    language=lang,
                    provider=provider,
                    model=model,
                    retrieved_docs=retrieved_docs,
                    weak_retrieval=weak_retrieval,
                )
                llm_ms = int((agent_main.time.perf_counter() - llm_started_at) * 1000)
                sources = agent_main._build_sources_from_docs(retrieved_docs)
                answer = agent_main._sanitize_answer_links(
                    answer,
                    agent_main._allowed_source_urls_from_docs(retrieved_docs),
                    lang,
                )
                agent_main.logger.info(
                    "Deterministic RAG complete: docs=%s, weak=%s, sources=%s",
                    len(retrieved_docs),
                    weak_retrieval,
                    len(sources),
                )

            db_metrics = agent_main.get_last_search_metrics() if answer_seeking else {}
            latency_breakdown = {
                "retrieval_invoke_ms": retrieval_ms,
                "llm_ms": llm_ms,
                "db_search": db_metrics,
            }
        finally:
            agent_main.reset_db_search_options(search_token)

        db_status = agent_main.get_last_search_status()
        if answer_seeking and not sources and db_status in {"schema_error", "infra_error", "error"}:
            agent_main.logger.warning(
                "Retrieval backend failure detected during deterministic path (status=%s).",
                db_status,
            )

        out_guard = validate_output(answer)
        if not out_guard.passed:
            answer = out_guard.reason
        elif out_guard.redacted:
            answer = out_guard.redacted

        return agent_main._response_payload(
            answer,
            thread_id=thread_id,
            started_at=started_at,
            sources=sources,
            latency_breakdown=latency_breakdown,
        )

    except Exception as exc:
        agent_main.logger.error("Error processing question '%s': %s", question, str(exc))
        agent_main.logger.error("Full traceback:\n%s", agent_main.traceback.format_exc())

        is_rate_limit = exc.__class__.__name__ in (
            "RateLimitError",
            "TooManyRequests",
            "RateLimitException",
        )
        if is_rate_limit:
            wait_seconds = 10.0
            match = agent_main.re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", str(exc))
            if match:
                try:
                    wait_seconds = float(match.group(1))
                except Exception:
                    pass
            if "lang" in locals() and lang == "es":
                fallback = f"El asistente está limitado por tasa temporalmente. Intenta nuevamente en {wait_seconds:.0f} segundos."
            else:
                fallback = f"The assistant is temporarily unavailable. Please try again in {wait_seconds:.0f} seconds."
            return agent_main._response_payload(
                fallback,
                thread_id=thread_id,
                started_at=started_at,
            )
        raise agent_main.HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/ask-stream")
async def ask_question_stream(
    question: str | None = agent_main.Query(
        default=None,
        description="Primary question text (use ``query`` only as a legacy alias).",
        openapi_examples=AGENT_ASK_QUESTION,
    ),
    query: str | None = agent_main.Query(
        default=None,
        description="Legacy alias for ``question`` when ``question`` is omitted.",
        openapi_examples=AGENT_ASK_QUERY_ALIAS,
    ),
    thread_id: str = agent_main.Query(
        default="default",
        description="Conversation thread id for correlating follow-ups.",
        openapi_examples=AGENT_ASK_THREAD_ID,
    ),
    lang: str | None = agent_main.Query(
        default=None,
        description="Force language (e.g. en, es) instead of auto-detection.",
        openapi_examples=AGENT_ASK_LANG,
    ),
    provider: str | None = agent_main.Query(
        default=None,
        description="LLM provider override (ollama-compatible stack).",
        openapi_examples=AGENT_ASK_PROVIDER,
    ),
    model: str | None = agent_main.Query(
        default=None,
        description="Model id override; must exist in ``GET /config`` when set.",
        openapi_examples=AGENT_ASK_MODEL,
    ),
    clarification_response: str | None = agent_main.Query(
        default=None,
        description="Reserved for future clarification flows.",
        openapi_examples=AGENT_ASK_CLARIFICATION_RESPONSE,
    ),
    context_answer: str | None = agent_main.Query(
        default=None,
        description="Prior assistant answer for short contextual follow-ups.",
        openapi_examples=AGENT_ASK_CONTEXT_ANSWER,
    ),
    tags: str | None = agent_main.Query(
        default=None,
        description="Comma-separated metadata tags for retrieval filtering.",
        openapi_examples=AGENT_ASK_TAGS,
    ),
    tag_match_mode: Literal["any", "all"] = agent_main.Query(
        default="any",
        description="Tag match mode: any|all",
        openapi_examples=AGENT_ASK_TAG_MATCH_MODE,
    ),
    include_untagged_fallback: bool = agent_main.Query(
        default=True,
        description="When tag filter is active, include untagged documents as fallback.",
        openapi_examples=AGENT_ASK_FLAG_TRUE,
    ),
    rerank: bool = agent_main.Query(
        default=False,
        description="Enable reranking of retrieved chunks.",
        openapi_examples=AGENT_ASK_FLAG_FALSE,
    ),
    rerank_top_k: int = agent_main.Query(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retain after reranking.",
        openapi_examples=AGENT_ASK_RERANK_TOP_K,
    ),
):
    """Stream agent progress and the final answer as SSE events."""
    del clarification_response

    question, query, lang, provider, model, tags, context_answer = (
        agent_main._coerce_ask_query_parameters(
            question=question,
            query=query,
            lang=lang,
            provider=provider,
            model=model,
            tags=tags,
            context_answer=context_answer,
        )
    )

    if question is None and query is not None:
        question = query
    if not question:
        raise agent_main.HTTPException(
            status_code=400,
            detail="Question parameter cannot be empty. Use 'question' or 'query'.",
        )

    async def generate_stream():
        lang_local = lang or "en"
        try:
            effective_provider, effective_model = agent_main._resolve_effective_provider_model(
                provider, model
            )

            def _sse(payload: dict) -> str:
                payload.setdefault(
                    "timestamp",
                    agent_main.datetime.now(agent_main.timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                )
                return f"data: {agent_main.json.dumps(payload)}\\n\\n"

            if not lang:
                lang_local = agent_main.detect_ask_query_language(question)

            if agent_main._is_non_linguistic_question(question):
                yield _sse(
                    {
                        "type": "complete",
                        "answer": agent_main._non_linguistic_query_reply(lang_local),
                        "sources": [],
                        "suggested_questions": [],
                        "thread_id": thread_id,
                        "plan": "",
                        "metadata": {"progress": 100, "stage": "complete"},
                    }
                )
                return

            agent_main.logger.info(
                "\n--- Streaming request received: '%s' (Language: %s, Thread: %s) ---",
                question,
                lang_local,
                thread_id,
            )

            msg = agent_main.get_agent_thinking_message("static_response", lang_local)
            yield _sse(
                {
                    "type": "thinking",
                    "message": msg,
                    "stage": "precheck",
                    "progress": 10,
                    "status": "working",
                    "waiting": False,
                }
            )

            msg = agent_main.get_agent_thinking_message("analyzing", lang_local)
            yield _sse(
                {
                    "type": "thinking",
                    "message": msg,
                    "stage": "analysis",
                    "progress": 25,
                    "status": "working",
                    "waiting": False,
                }
            )
            answer_seeking = agent_main._is_answer_seeking_query(question, lang_local)
            contextual_follow_up = bool(context_answer) and agent_main._is_contextual_follow_up(
                question, lang_local
            )
            agent_main.logger.info("Streaming intent gate: answer_seeking=%s", answer_seeking)

            if contextual_follow_up:
                answer = await asyncio.to_thread(
                    agent_main._build_contextual_follow_up_answer,
                    question=question,
                    prior_answer=context_answer or "",
                    language=lang_local,
                    provider=effective_provider,
                    model=effective_model,
                )

                yield _sse(
                    {
                        "type": "complete",
                        "answer": answer,
                        "sources": [],
                        "suggested_questions": agent_main._build_follow_up_suggestions(
                            question=question,
                            answer=answer,
                            language=lang_local,
                            sources=[],
                        ),
                        "thread_id": thread_id,
                        "plan": "",
                        "metadata": {"progress": 100, "stage": "complete"},
                    }
                )
                return

            if not answer_seeking:
                local_static = agent_main._find_static_faq_answer(question, lang_local)
                if local_static:
                    agent_main.logger.info(
                        "Returning static FAQ answer (streaming, non-answer intent)."
                    )
                    yield _sse(
                        {
                            "type": "complete",
                            "answer": local_static,
                            "sources": [],
                            "suggested_questions": agent_main._build_follow_up_suggestions(
                                question=question,
                                answer=local_static,
                                language=lang_local,
                                sources=[],
                            ),
                            "thread_id": thread_id,
                            "plan": "",
                            "metadata": {"progress": 100, "stage": "complete"},
                        }
                    )
                    return

            sources: list[dict] = []
            plan = ""

            if not answer_seeking:
                local_non_answer = agent_main._find_static_faq_answer(question, lang_local)
                if local_non_answer:
                    answer = local_non_answer
                else:
                    llm_plain = agent_main._get_llm_without_tools(
                        effective_provider, effective_model
                    )
                    quick_prompt = f"Respond briefly and naturally in {'Spanish' if lang_local == 'es' else 'English'}: {question}"
                    plain = await asyncio.to_thread(
                        llm_plain.invoke,
                        [agent_main.HumanMessage(content=quick_prompt)],
                    )
                    answer = plain.content if hasattr(plain, "content") else str(plain)
            else:
                tool_msg = agent_main.get_agent_thinking_message("db_search", lang_local)
                yield _sse(
                    {
                        "type": "thinking",
                        "message": tool_msg,
                        "stage": "tooling",
                        "progress": 40,
                        "status": "working",
                        "waiting": False,
                        "tool": "db_search",
                    }
                )
                yield _sse(
                    {
                        "type": "tool_event",
                        "phase": "start",
                        "tool": "db_search",
                        "message": tool_msg,
                        "stage": "tooling",
                        "progress": 42,
                        "status": "working",
                        "transient": True,
                        "waiting": True,
                    }
                )

                request_tags = agent_main.parse_tags_input(tags)
                search_token = agent_main.set_db_search_options(
                    tags=request_tags,
                    tag_match_mode=tag_match_mode,
                    include_untagged_fallback=include_untagged_fallback,
                    rerank=rerank,
                    rerank_top_k=rerank_top_k,
                )
                try:
                    raw_search = await asyncio.to_thread(
                        agent_main.db_search_tool.invoke, {"query": question}
                    )
                finally:
                    agent_main.reset_db_search_options(search_token)

                raw_search_text = raw_search if isinstance(raw_search, str) else str(raw_search)
                retrieved_docs = agent_main._parse_db_search_docs(raw_search_text)
                weak_retrieval = agent_main._is_weak_retrieval(retrieved_docs)

                yield _sse(
                    {
                        "type": "tool_event",
                        "phase": "result",
                        "tool": "db_search",
                        "message": agent_main._summarize_tool_result(
                            "db_search", raw_search_text, lang_local
                        ),
                        "stage": "tooling",
                        "progress": 62,
                        "status": "working",
                        "transient": True,
                        "waiting": False,
                    }
                )

                answer = await asyncio.to_thread(
                    agent_main._build_deterministic_rag_answer,
                    question=question,
                    language=lang_local,
                    provider=effective_provider,
                    model=effective_model,
                    retrieved_docs=retrieved_docs,
                    weak_retrieval=weak_retrieval,
                )
                sources = agent_main._build_sources_from_docs(retrieved_docs)
                answer = agent_main._sanitize_answer_links(
                    answer,
                    agent_main._allowed_source_urls_from_docs(retrieved_docs),
                    lang_local,
                )
                agent_main.logger.info(
                    "Streaming deterministic RAG complete: docs=%s, weak=%s, sources=%s",
                    len(retrieved_docs),
                    weak_retrieval,
                    len(sources),
                )

            yield _sse(
                {
                    "type": "thinking",
                    "message": (
                        "Finalizing answer..." if lang_local != "es" else "Finalizando respuesta..."
                    ),
                    "stage": "finalizing",
                    "progress": 95,
                    "status": "working",
                    "waiting": False,
                }
            )

            yield _sse(
                {
                    "type": "complete",
                    "answer": answer,
                    "sources": sources,
                    "suggested_questions": agent_main._build_follow_up_suggestions(
                        question=question,
                        answer=answer,
                        language=lang_local,
                        sources=sources,
                    ),
                    "thread_id": thread_id,
                    "plan": plan,
                    "metadata": {"progress": 100, "stage": "complete"},
                }
            )

        except Exception as exc:
            agent_main.logger.error("Error in streaming endpoint '%s': %s", question, str(exc))
            agent_main.logger.error("Full traceback:\n%s", agent_main.traceback.format_exc())

            is_rate_limit = exc.__class__.__name__ in (
                "RateLimitError",
                "TooManyRequests",
                "RateLimitException",
            )
            if is_rate_limit:
                fallback = (
                    "Servicio temporalmente no disponible. Inténtalo de nuevo en un momento."
                    if lang_local == "es"
                    else "Service temporarily unavailable. Please try again in a moment."
                )
            else:
                fallback = (
                    f"Error procesando la pregunta: {str(exc)}"
                    if lang_local == "es"
                    else f"Error processing question: {str(exc)}"
                )

            yield _sse(
                {
                    "type": "error",
                    "message": fallback,
                    "stage": "error",
                    "progress": 100,
                    "status": "error",
                }
            )

    return agent_main.StreamingResponse(generate_stream(), media_type="text/event-stream")
