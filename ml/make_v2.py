"""ml/make_v2.py —— v2：保持 val/test 不变，仅训练集去除重复内容分组。"""

import csv
import re
import shutil
from pathlib import Path


def norm_key(t):
    t = t.lower()
    t = re.sub(r"https?://\S+|www\.\S+", "<URL>", t)
    t = re.sub(r"[\W_]+", " ", t)
    return " ".join(t.split())


def read_csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


train = read_csv("data/processed/train.csv")
seen, kept, removed = set(), [], 0
for row in train:
    k = norm_key(row["text"])
    if k in seen:
        removed += 1
        continue
    seen.add(k)
    kept.append(row)

Path("data/v2").mkdir(parents=True, exist_ok=True)
# val/test 直接从 v1 复制，保证评估集字节级不变
for name in ("val", "test"):
    shutil.copyfile(f"data/v1/{name}.csv", f"data/v2/{name}.csv")
with open("data/v2/train.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["text", "label"])
    w.writeheader()
    w.writerows(kept)
print(f"[v2] 训练集 {len(train)} -> {len(kept)}（去重 {removed} 条）")
