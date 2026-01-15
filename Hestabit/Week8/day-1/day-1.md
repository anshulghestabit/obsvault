# WEEK 8 — LLM FINE-TUNING, QUANTISATION & OPTIMISED INFERENCE

### OBJECTIVES
* LLM internals
* Parameter-efficient fine-tuning (LoRA / QLoRA)
* Quantisation (8-bit, 4-bit, GGUF)
* Inference optimization
* Deployment

### MODELS (Mandatory)
Phi-2, Mistral 7B, TinyLlama, or Qwen

---

# DAY 1 — LLM ARCHITECTURE + DATA PREP FOR FINE-TUNING

### Learning Outcomes
* LLM anatomy
* Tokenization
* Instruction tuning

### Exercise
Build your **instruction tuning dataset**:
* 3 types: QA, Reasoning, Extraction
* 1,000 samples (Clean + curated)
* JSONL format

### Deliverables
* `/data/train.jsonl`
* `/utils/data_cleaner.py`
* `DATASET-ANALYSIS.md`
