from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from config import LOCAL_MODEL

_tokenizer = None
_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def _load_model():
    global _tokenizer, _model
    if _model is None or _tokenizer is None:
        print(f"Loading local model to {_device}...")
        _tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL)
        
        load_kwargs = {
            "low_cpu_mem_usage": True,
            "torch_dtype": torch.float16 if _device == "cuda" else torch.float32,
        }
        
        _model = AutoModelForCausalLM.from_pretrained(LOCAL_MODEL, **load_kwargs).to(_device)
        print("Local model loaded")
    return _tokenizer, _model


def generate_local(system_prompt, user_prompt):
    tokenizer, model = _load_model()

    # TinyLlama Chat Template format
    prompt = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(_device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode only the NEW tokens
    generated_ids = outputs[0][inputs.input_ids.shape[-1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)

    return response.strip()