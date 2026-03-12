import json
import random
import os
from transformers import AutoTokenizer
import matplotlib.pyplot as plt

INPUT_FILE="data/raw/coding_dataset.jsonl"

os.makedirs("data",exist_ok=True)
os.makedirs("reports",exist_ok=True)

random.seed(42)

tokenizer=AutoTokenizer.from_pretrained("bert-base-uncased")

data=[]
with open(INPUT_FILE) as f:
    for line in f:
        data.append(json.loads(line))

clean=[]
lengths=[]

for item in data:

    instruction=item.get("instruction","")
    input_text=item.get("input","")
    output=item.get("output","")

    if not instruction:
        continue

    if len(output)<5:
        continue

    text=instruction+" "+input_text+" "+output

    tokens=len(tokenizer.encode(text))
    lengths.append(tokens)

    if tokens>512:
        continue

    clean.append(item)

random.shuffle(clean)

split=int(len(clean)*0.9)

train=clean[:split]
val=clean[split:]

with open("data/train.jsonl","w") as f:
    for x in train:
        f.write(json.dumps(x)+"\n")

with open("data/val.jsonl","w") as f:
    for x in val:
        f.write(json.dumps(x)+"\n")

plt.hist(lengths,bins=40)
plt.title("Token Length Distribution")
plt.savefig("reports/token_distribution.png")

print("Total:",len(clean))
print("Train:",len(train))
print("Val:",len(val))
print("Max tokens:",max(lengths))
print("Avg tokens:",sum(lengths)/len(lengths))