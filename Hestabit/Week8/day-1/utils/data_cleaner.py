import os
import json
import numpy as np
from datasets import load_from_disk, load_dataset, concatenate_datasets

SEED = 42
SAMPLES_PER_TYPE = 500 ## From each Dataset taking 500 samples Each ..
OUTPUT_DIR = "data"

np.random.seed(SEED)


def format_qa(example):
    """Normalize QA samples into the shared instruction format."""
    try:
        return {
            "instruction": "Answer the medical question accurately.",
            "input": example["input"],
            "output": example["output"]
        }
    except KeyError as exc:
        raise KeyError(f"missing required QA field: {exc.args[0]}") from exc
    except TypeError as exc:
        raise TypeError("QA example must be a mapping") from exc


def format_reasoning(example):
    """Normalize reasoning samples into the shared instruction format."""
    try:
        return {
            "instruction": "Answer the medical question with step-by-step reasoning.",
            "input": example["Question"],
            "output": example["Complex_CoT"] + "\nFinal Answer: " + example["Response"]
        }
    except KeyError as exc:
        raise KeyError(f"missing required reasoning field: {exc.args[0]}") from exc
    except TypeError as exc:
        raise TypeError("reasoning example must be a mapping") from exc


def format_extraction(example):
    """Normalize extraction samples into the shared instruction format."""
    try:
        return {
            "instruction": "Extract the drug name and adverse events from the report.",
            "input": example["input"],
            "output": example["output"]
        }
    except KeyError as exc:
        raise KeyError(f"missing required extraction field: {exc.args[0]}") from exc
    except TypeError as exc:
        raise TypeError("extraction example must be a mapping") from exc


def token_length(sample):
    """Return the whitespace token count for one normalized sample."""
    try:
        text = f"{sample['instruction']} {sample['input']} {sample['output']}"
        return len(text.split())
    except KeyError as exc:
        raise KeyError(f"missing required sample key: {exc.args[0]}") from exc
    except TypeError as exc:
        raise TypeError("sample must be a mapping with instruction, input, and output") from exc


def save_jsonl(samples, path):
    """Write samples to a JSONL file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            for sample in samples:
                try:
                    f.write(json.dumps(sample) + "\n")
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"sample is not JSON serializable for {path}") from exc
    except OSError as exc:
        raise OSError(f"unable to write JSONL file: {path}") from exc


def main():
    """Build cleaned train and validation datasets from raw sources."""
    try:
        qa_ds = load_from_disk("../raw-data/qa_medical_flashcards")
        qa_ds = qa_ds.shuffle(seed=SEED).select(range(SAMPLES_PER_TYPE))
        qa_ds = qa_ds.map(format_qa)

        reasoning_ds = load_from_disk("../raw-data/reasoning_medical_o1")
        reasoning_ds = reasoning_ds.shuffle(seed=SEED).select(range(SAMPLES_PER_TYPE))
        reasoning_ds = reasoning_ds.map(format_reasoning)

        extraction_ds = load_dataset(
            "json",
            data_files="../raw-data/Extraction_dataset/extraction.json",
            split="train"
        )
        extraction_ds = extraction_ds.shuffle(seed=SEED).select(range(SAMPLES_PER_TYPE))
        extraction_ds = extraction_ds.map(format_extraction)

        ##Here i have merged the Datasets:->
        final_ds = concatenate_datasets([qa_ds, reasoning_ds, extraction_ds])

        lengths = [token_length(s) for s in final_ds]
        if not lengths:
            raise ValueError("combined dataset is empty")

        max_len = np.percentile(lengths, 95)

        cleaned = [
            s for s, l in zip(final_ds, lengths) if l <= max_len
        ]
        if not cleaned:
            raise ValueError("no samples remain after length filtering")

        np.random.shuffle(cleaned)

        ##Train/val split :->
        split_idx = int(len(cleaned) * 0.9)
        train_samples = cleaned[:split_idx]
        val_samples = cleaned[split_idx:]

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        save_jsonl(train_samples, os.path.join(OUTPUT_DIR, "train.jsonl"))
        save_jsonl(val_samples, os.path.join(OUTPUT_DIR, "val.jsonl"))

        print(f"Total samples after cleaning: {len(cleaned)}")
        print(f"Train samples: {len(train_samples)}")
        print(f"Validation samples: {len(val_samples)}")
    except Exception as exc:
        print(f"Data cleaning failed: {exc}")
        raise


if __name__ == "__main__":
    main()
