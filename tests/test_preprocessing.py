"""tests/test_preprocessing.py —— 数据/分组键检查（B 负责）"""

import csv
import json
import re


def norm_key(t):
    t = t.lower()
    t = re.sub(r"https?://\S+|www\.\S+", "<URL>", t)
    t = re.sub(r"[\W_]+", " ", t)
    return " ".join(t.split())


def read_split(name, version="v2"):
    with open(f"data/{version}/{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_labels_valid_and_text_nonempty():
    for name in ("train", "val", "test"):
        rows = read_split(name)
        assert all(r["label"] in ("ham", "spam") for r in rows)
        assert all(r["text"].strip() for r in rows)


def test_no_group_key_overlap_between_splits():
    keys = {n: {norm_key(r["text"]) for r in read_split(n)} for n in ("train", "val", "test")}
    assert not (keys["train"] & keys["val"])
    assert not (keys["train"] & keys["test"])
    assert not (keys["val"] & keys["test"])


def test_split_report_matches_files():
    # split_report 描述的是原始 70/15/15 划分（v1），v1 未做去重，数量应一致
    report = json.load(open("data/processed/split_report.json", encoding="utf-8"))
    for name in ("train", "val", "test"):
        assert len(read_split(name, version="v1")) == report["splits"][name]["samples"]


def test_v2_val_test_identical_to_v1():
    # 评估集必须字节级不变，v1/v2 测试集才可公平比较
    for name in ("val", "test"):
        a = open(f"data/v1/{name}.csv", "rb").read()
        b = open(f"data/v2/{name}.csv", "rb").read()
        assert a == b


def test_v2_train_is_deduped():
    rows = read_split("train", version="v2")
    keys = [norm_key(r["text"]) for r in rows]
    assert len(keys) == len(set(keys)), "v2 训练集不应存在重复内容分组"
