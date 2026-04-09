from llama_cpp import Llama
from threading import Lock
from deploy.config import MODEL_PATH, CONTEXT_WINDOW

_model = None
_lock = Lock()


def get_model():
    """Load and cache the GGUF model instance."""

    global _model

    try:
        if _model is None:
            with _lock:
                if _model is None:
                    if not MODEL_PATH.exists():
                        raise FileNotFoundError(f"model file not found: {MODEL_PATH}")

                    print("Loading GGUF model into memory...")
                    # Here Llama is a high level python wrapper that loads the model from a MODEL_PATH ..
                    _model = Llama(
                        model_path=str(MODEL_PATH),
                        n_ctx=CONTEXT_WINDOW,
                        n_threads=None,
                        verbose=False
                    )
                    print("GGUF model loaded successfully")

        return _model
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError("failed to initialize GGUF model") from exc
