import os
import time
from llama_cpp import Llama


MODEL_PATH = "../quantized/model.gguf"  
PROMPT = "Explain hypertension step by step and its complications."
MAX_TOKENS = 128
N_CTX = 2048



def get_model_size(path):
    """Return the GGUF model size in gigabytes."""
    try:
        size_bytes = os.path.getsize(path)
        return round(size_bytes / (1024 ** 3), 2)  # GB
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"model file not found: {path}") from exc
    except OSError as exc:
        raise OSError(f"unable to access model file: {path}") from exc


def benchmark_gguf_cpu():
    """Run a simple CPU benchmark for the quantized GGUF model."""
    try:
        print("Loading GGUF model (CPU)...")

        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=os.cpu_count() or 1,
            verbose=False
        )

        print("Running inference...")
        start = time.time()

        output = llm(
            PROMPT,
            max_tokens=MAX_TOKENS,
            temperature=0.0
        )

        end = time.time()
        elapsed = end - start
        if elapsed <= 0:
            raise ValueError("benchmark timing must be greater than zero")

        try:
            tokens_generated = output["usage"]["completion_tokens"]
            sample_text = output["choices"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("model output is missing expected fields") from exc

        tokens_per_sec = tokens_generated / elapsed

        print("\n===== GGUF CPU BENCHMARK =====")
        print(f"Model size     : {get_model_size(MODEL_PATH)} GB")
        print(f"Tokens/sec     : {tokens_per_sec:.2f}")
        print("\n===== SAMPLE OUTPUT =====")
        print(sample_text)
    except Exception as exc:
        print(f"GGUF CPU benchmark failed: {exc}")
        raise


if __name__ == "__main__":
    benchmark_gguf_cpu()
