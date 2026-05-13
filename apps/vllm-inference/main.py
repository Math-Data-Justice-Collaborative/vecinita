"""vLLM inference service — Modal app with OpenAI-compatible API."""
import modal

MINUTES = 60

app = modal.App("vecinita-vllm-inference")

vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm>=0.8.0",
        "huggingface_hub[hf_transfer]",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache_vol = modal.Volume.from_name("vecinita-hf-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vecinita-vllm-cache", create_if_missing=True)


@app.cls(
    image=vllm_image,
    gpu=modal.gpu.A100(count=1, size="40GB"),
    scaledown_window=15 * MINUTES,
    timeout=30 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=32, target_inputs=8)
class Inference:
    @modal.enter()
    def start_vllm(self):
        import os, subprocess, socket, time

        self.model = os.environ.get("VLLM_MODEL", "")
        if not self.model:
            raise RuntimeError("VLLM_MODEL environment variable must be set")
        self.port = 8000
        cmd = [
            "python",
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            self.model,
            "--served-model-name",
            self.model,
            "--host",
            "0.0.0.0",
            "--port",
            str(self.port),
            "--gpu-memory-utilization",
            os.environ.get("VLLM_GPU_MEMORY_UTIL", "0.85"),
            "--max-model-len",
            os.environ.get("VLLM_MAX_MODEL_LEN", "4096"),
        ]
        self.proc = subprocess.Popen(cmd)
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=1).close()
                return
            except OSError:
                if self.proc.poll() is not None:
                    raise RuntimeError(
                        f"vLLM exited with code {self.proc.returncode}"
                    )
            time.sleep(2)
        raise TimeoutError("vLLM did not start within timeout")

    @modal.web_server(port=8000, startup_timeout=30 * MINUTES)
    def serve(self):
        pass

    @modal.exit()
    def stop(self):
        if hasattr(self, "proc") and self.proc.poll() is None:
            self.proc.terminate()
