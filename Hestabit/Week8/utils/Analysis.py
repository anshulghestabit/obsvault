import json
import os
from collections import Counter
import matplotlib.pyplot as plt


DATA_PATH = "../data/train.jsonl"
OUTPUT_DIR = "../outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def classify_task(instruction):
    """Classify an instruction into a simple task bucket."""
    try:
        inst = instruction.lower()
    except AttributeError as exc:
        raise TypeError("instruction must be a string") from exc

    if "extract" in inst:
        return "extraction"
    if "step-by-step" in inst or "step by step" in inst or "reasoning" in inst:
        return "reasoning"
    return "qa"


def token_length(sample):
    """Return the whitespace token count for one training sample."""
    try:
        text = f"{sample['instruction']} {sample['input']} {sample['output']}"
        return len(text.split())
    except KeyError as exc:
        raise KeyError(f"missing required sample key: {exc.args[0]}") from exc
    except TypeError as exc:
        raise TypeError("sample must be a mapping with instruction, input, and output") from exc


def load_data():
    """Load JSONL samples from disk."""
    samples = []

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSON on line {line_number} in {DATA_PATH}"
                    ) from exc
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"data file not found: {DATA_PATH}") from exc
    except OSError as exc:
        raise OSError(f"unable to read data file: {DATA_PATH}") from exc

    return samples


def plot_token_distribution(samples):
    """Plot and save token-length distribution stats."""
    try:
        lengths = [token_length(s) for s in samples]
        if not lengths:
            raise ValueError("samples cannot be empty")

        plt.figure()
        plt.hist(lengths, bins=40)
        plt.xlabel("Token Length")
        plt.ylabel("Count")
        plt.title("Token Length Distribution (Train Set)")
        plt.savefig(os.path.join(OUTPUT_DIR, "token_length_distribution.png"))
        plt.close()

        print(
            f"Token stats -> min: {min(lengths)}, "
            f"max: {max(lengths)}, "
            f"avg: {sum(lengths)//len(lengths)}"
        )
    except (KeyError, TypeError, ValueError):
        raise
    except OSError as exc:
        raise OSError("failed to save token length distribution plot") from exc


def plot_task_distribution(samples):
    """Plot and save instruction-type distribution stats."""
    try:
        tasks = [classify_task(s["instruction"]) for s in samples]
        if not tasks:
            raise ValueError("samples cannot be empty")

        counts = Counter(tasks)

        plt.figure()
        plt.bar(counts.keys(), counts.values())
        plt.xlabel("Task Type")
        plt.ylabel("Count")
        plt.title("Instruction Type Distribution (QA / Reasoning / Extraction)")
        plt.savefig(os.path.join(OUTPUT_DIR, "task_type_distribution.png"))
        plt.close()
    except (KeyError, TypeError, ValueError):
        raise
    except OSError as exc:
        raise OSError("failed to save task type distribution plot") from exc


def main():
    """Run the full analysis pipeline."""
    try:
        samples = load_data()
        plot_token_distribution(samples)
        plot_task_distribution(samples)
        print("Day-1 analysis plots saved in outputs/")
    except Exception as exc:
        print(f"Analysis failed: {exc}")
        raise


if __name__ == "__main__":
    main()
