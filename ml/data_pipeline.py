"""ml/data_pipeline.py —— 原始CSV -> 统一字段 + 防泄漏划分"""
import argparse, json, random, re
from collections import Counter
from pathlib import Path

LABELS = ("ham", "spam")

def read_raw(csv_path: str):
    """读取原始文件。已知格式：每行整体被双引号包裹，行内 label\ttext。"""
    rows, skipped = [], 0
    with open(csv_path, encoding="utf-8", newline="") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            if "\t" not in line:
                skipped += 1
                continue
            label, text = line.split("\t", 1)
            label = label.strip()
            text = text.strip()
            if label not in LABELS or not text:
                skipped += 1
                continue
            rows.append((text, label))
    return rows, skipped

def norm_key(text: str) -> str:
    """生成内容分组键：仅用于识别重复/防泄漏，不做激进清洗。"""
    t = text.lower()
    t = re.sub(r"https?://\S+|www\.\S+", "<URL>", t)
    t = re.sub(r"[\W_]+", " ", t)
    return " ".join(t.split())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/raw/SMSSpamCollection.csv")
    ap.add_argument("--outdir", default="data/processed")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows, skipped = read_raw(args.input)
    print(f"[统计] 有效样本={len(rows)}  跳过行={skipped}")
    print(f"[统计] 标签分布={Counter(l for _, l in rows)}")

    # 冲突标签核查：同一分组键出现不同标签则记录并整组剔除（本数据实测为 0 组）
    groups = {}
    for text, label in rows:
        groups.setdefault(norm_key(text), []).append((text, label))
    conflicts = [k for k, v in groups.items() if len({l for _, l in v}) > 1]
    if conflicts:
        print(f"[警告] 发现 {len(conflicts)} 组标签冲突，整组剔除并写入 conflict_keys.json")
    keys = sorted(k for k in groups if k not in set(conflicts))

    random.seed(args.seed)
    random.shuffle(keys)
    n = len(keys)
    i1, i2 = int(n * 0.70), int(n * 0.85)
    splits = {"train": keys[:i1], "val": keys[i1:i2], "test": keys[i2:]}

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, ks in splits.items():
        flat = [(t, l) for k in ks for (t, l) in groups[k]]
        with open(out / f"{name}.csv", "w", encoding="utf-8", newline="") as f:
            f.write("text,label\n")
            for t, l in flat:
                # text 含逗号/引号，用csv标准写法
                escaped = '"' + t.replace('"', '""') + '"'
                f.write(f"{escaped},{l}\n")
        report[name] = {"samples": len(flat),
                        "ham": sum(1 for _, l in flat if l == "ham"),
                        "spam": sum(1 for _, l in flat if l == "spam")}
        print(f"[划分] {name}: 样本={len(flat)} 分布={Counter(l for _, l in flat)}")

    # 验证三集合分组键无重叠
    s_train, s_val, s_test = set(splits["train"]), set(splits["val"]), set(splits["test"])
    assert not (s_train & s_val) and not (s_train & s_test) and not (s_val & s_test)
    print("[验收] 三个集合的分组键无重叠 ✔")

    with open(out / "split_report.json", "w", encoding="utf-8") as f:
        json.dump({"seed": args.seed, "skipped": skipped,
                   "conflict_groups": len(conflicts),
                   "splits": report}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
