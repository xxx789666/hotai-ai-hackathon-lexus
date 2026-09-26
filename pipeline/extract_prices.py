"""從售後語料抽含金額句子，規則標成原廠／外廠與保養項目。

不呼叫 LLM。金額語料是論壇口述，不是官方定價。

用法：python pipeline/extract_prices.py
輸出：data/processed/price_mentions.jsonl
      data/processed/price_summary.json（統計，供報告引用）
"""
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.verify_churn import build_context  # noqa: E402

P = ROOT / "data" / "processed"
OUT = P / "price_mentions.jsonl"
SUMMARY = P / "price_summary.json"

# 任務指定的金額正則（三擇一）。
# k/K 必須獨立，避免把 100km、30kg 當成 100k、30k。
AMOUNT_RE = re.compile(
    r"\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?\s*(?:[kK](?![A-Za-z])|萬)|\d{3,6}\s*(?:元|塊|NT|nt)"
)

# --- 詞表（可調）---
# 對象：整句只有一類線索時，該句每個金額都用這一類（對應「句中有」）。
# 同一句同時有原廠與外廠線索時，改看該金額離哪一類詞最近，避免
# 「原廠 8 千、外廠 3 千」整句被標成同一邊。
OEM_PATTERNS = [
    re.compile(r"原廠"),
    re.compile(r"服務廠"),
    re.compile(r"[Ll]exus\s*廠"),
    re.compile(r"LEXUS\s*廠"),
    re.compile(r"和泰"),
    re.compile(r"定保"),
]
# 「原廠技師」不是外廠；「保養廠」前若已是「原廠」也不算外廠。
EXT_PATTERNS = [
    re.compile(r"外廠"),
    re.compile(r"外面"),
    re.compile(r"(?<!原廠)保養廠"),
    re.compile(r"車業"),
    re.compile(r"(?<!原廠)技師"),
    re.compile(r"輪胎行"),
    re.compile(r"汽車百貨"),
    re.compile(r"蝦皮"),
    re.compile(r"自己買"),
    re.compile(r"自備"),
]

# 項目：較具體的詞優先。同一句多個項目時，取離該金額最近者。
# 「保養」不吃掉「保養廠」。
ITEM_PATTERNS = [
    ("鈑烤", re.compile(r"鈑烤|板烤|鈑金|板金|烤漆|噴漆|板噴")),
    ("變速箱", re.compile(r"變速箱|變速器|自排油|變速箱油")),
    ("避震", re.compile(r"避震")),
    ("冷氣", re.compile(r"冷氣|空調|冷媒|壓縮機")),
    ("輪胎", re.compile(r"輪胎|車胎|換胎|胎皮|米其林|橫濱|普利司通")),
    ("電瓶", re.compile(r"電瓶|蓄電池|小電池|啟動電池")),
    ("煞車", re.compile(r"來令片|來令|煞車皮|碟盤|煞車盤|煞車")),
    ("機油", re.compile(r"機油|機濾|機油芯")),
    ("定保", re.compile(r"定期保養|定保|小保養|大保養|保養套餐|保養(?!廠)")),
    ("零件", re.compile(r"零件|正廠件|副廠")),
]

MASK_RES = [
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[email]"),
    (re.compile(r"https?://\S+|www\.[A-Za-z0-9.\-]+\S*", re.I), "[網址]"),
    (re.compile(r"(?<![A-Za-z0-9._%+\-])@[A-Za-z0-9_.]{3,}"), "[帳號]"),
    (re.compile(r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}"), "[電話]"),
]


def mask_light(text):
    if not text:
        return text
    for cre, repl in MASK_RES:
        text = cre.sub(repl, text)
    return text


def to_twd(raw: str):
    m = re.match(r"(\d+(?:\.\d+)?)\s*([kK萬])", raw)
    if m:
        n = float(m.group(1))
        return int(round(n * (1000 if m.group(2) in "kK" else 10000)))
    if "," in raw:
        return int(raw.replace(",", ""))
    m = re.match(r"(\d{3,6})", raw)
    return int(m.group(1)) if m else None


CLAUSE_SEPS = "，。！？；、\n"


def clause_bounds(text, start, end):
    a = 0
    for s in CLAUSE_SEPS:
        p = text.rfind(s, 0, start)
        if p >= a:
            a = p + 1 if p >= 0 else 0
    b = len(text)
    for s in CLAUSE_SEPS:
        p = text.find(s, end)
        if p != -1 and p < b:
            b = p
    return a, b


def keep_amount(text, start, end, raw, value):
    if value is None or value < 300 or value > 500_000:
        return False
    # 車價：帶「萬」且超過 50 萬（與上列上限同一門檻，明示保留）。
    if "萬" in raw and value > 500_000:
        return False
    after = text[end:end + 8]
    before = text[max(0, start - 6):start]
    if re.match(r"^\s*(多\s*)?(公里|km|KM|英里|英哩|哩)", after):
        return False
    if "萬" in raw and re.match(r"^\s*初", after):
        return False
    # 整數「12萬就…」多半是里程，不是報價；「1.2萬」「1萬多」「要 8 萬」才留。
    if re.fullmatch(r"\d+\s*萬", raw) and not re.match(r"^\s*(元|塊|多)", after):
        if not re.search(r"(要|收|花|價|報|約|大概|只要|貴|便宜|索|開|喊|付|算)$", before):
            return False
    # 年份、百分比、次數、規格不是保養費用。
    if re.match(r"^\s*(年|月|日|次|%|％|度|項|顆|條|組|人|台|臺|轉|匹|cc|CC)", after):
        return False
    # 里程間隔：每 8 萬、跑 12 萬、4 萬保養（保養里程，不是報價）。
    if "萬" in raw and re.search(r"(每|跑|駛|里程|開了|開到|來到)$", before):
        return False
    if "萬" in raw and re.match(r"^\s*(保養|定保|檢查|進廠|回廠|公里)", after):
        if value >= 40_000:
            return False
    a, b = clause_bounds(text, start, end)
    clause = text[a:b]
    if re.search(r"月薪|年薪|薪水|月入|底薪|時薪|油耗|油費|利息|頭期款|貸款", clause):
        return False
    return True


def hits(text, patterns):
    found = []
    for cre in patterns:
        for m in cre.finditer(text):
            found.append((m.start(), m.end()))
    return found


def nearest(cues, start, end):
    """cues: list of (start, end, label)."""
    center_best = None
    for s, e, lab in cues:
        if e <= start:
            dist = start - e
        elif s >= end:
            dist = s - end
        else:
            dist = 0
        if center_best is None or dist < center_best[0]:
            center_best = (dist, lab)
    return center_best[1] if center_best else "不明"


def _in_clause(spans, a, b):
    return [(s, e) for s, e in spans if s >= a and e <= b]


def label_party(text, start, end):
    oem_all = hits(text, OEM_PATTERNS)
    ext_all = hits(text, EXT_PATTERNS)
    if oem_all and not ext_all:
        return "原廠"
    if ext_all and not oem_all:
        return "外廠"
    if not oem_all and not ext_all:
        return "不明"
    # 同一句兩邊都有：用該金額所在分句（沒有再看前一個分句）。
    a, b = clause_bounds(text, start, end)
    oem = _in_clause(oem_all, a, b)
    ext = _in_clause(ext_all, a, b)
    if not oem and not ext and a > 0:
        pa, _pb = clause_bounds(text, a - 1, a - 1)
        oem = _in_clause(oem_all, pa, a)
        ext = _in_clause(ext_all, pa, a)
    if oem and not ext:
        return "原廠"
    if ext and not oem:
        return "外廠"
    if not oem and not ext:
        return "不明"
    cues = [(s, e, "原廠") for s, e in oem] + [(s, e, "外廠") for s, e in ext]
    return nearest(cues, start, end)


def label_item(text, start, end):
    all_cues = []
    for name, cre in ITEM_PATTERNS:
        for m in cre.finditer(text):
            all_cues.append((m.start(), m.end(), name))
    if not all_cues:
        return "不明"
    kinds = {lab for _, _, lab in all_cues}
    if len(kinds) == 1:
        return next(iter(kinds))
    a, b = clause_bounds(text, start, end)
    local = [c for c in all_cues if c[0] >= a and c[1] <= b]
    if not local and a > 0:
        pa, _pb = clause_bounds(text, a - 1, a - 1)
        local = [c for c in all_cues if c[0] >= pa and c[1] <= a]
    if not local:
        return "不明"
    if len({lab for _, _, lab in local}) == 1:
        return local[0][2]
    return nearest(local, start, end)


def load_deid():
    deid = {}
    with open(P / "aftersales_deid.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            deid[r["sid"]] = r.get("text") or ""
    return deid


def iter_aftersales():
    with open(P / "aftersales.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def quartile(xs):
    xs = sorted(xs)
    if not xs:
        return None, None, None
    med = int(statistics.median(xs))
    if len(xs) == 1:
        return med, med, med
    q1, _q2, q3 = statistics.quantiles(xs, n=4, method="inclusive")
    return med, int(round(q1)), int(round(q3))


def pick_examples(rows, k=3):
    """每個項目挑接近中位數的 deid 句，盡量含原廠與外廠。"""
    chosen = []
    used = set()
    for party in ("原廠", "外廠", "不明"):
        pool = [r for r in rows if r["party"] == party and r["sid"] not in used]
        if not pool:
            continue
        vals = [r["amount"] for r in pool]
        med = statistics.median(vals)
        pool.sort(key=lambda r: (abs(r["amount"] - med), len(r["text"])))
        for r in pool:
            if r["sid"] in used:
                continue
            if len(r["text"]) < 8:
                continue
            chosen.append(r)
            used.add(r["sid"])
            break
        if len(chosen) >= k:
            break
    if len(chosen) < k:
        rest = sorted(rows, key=lambda r: len(r["text"]))
        for r in rest:
            if r["sid"] in used:
                continue
            chosen.append(r)
            used.add(r["sid"])
            if len(chosen) >= k:
                break
    return chosen[:k]


def main():
    deid = load_deid()
    mentions = []
    n_sent = 0
    for row in iter_aftersales():
        n_sent += 1
        text = row.get("text") or ""
        for m in AMOUNT_RE.finditer(text):
            raw = m.group(0)
            value = to_twd(raw)
            if not keep_amount(text, m.start(), m.end(), raw, value):
                continue
            sid = row["sid"]
            mentions.append({
                "sid": sid,
                "amount": value,
                "raw": raw,
                "party": label_party(text, m.start(), m.end()),
                "item": label_item(text, m.start(), m.end()),
                "text_src": text,
            })

    sids = [m["sid"] for m in mentions]
    ctx = build_context(sids) if sids else {}

    with open(OUT, "w", encoding="utf-8") as f:
        for m in mentions:
            c = ctx.get(m["sid"]) or {}
            sentence = deid.get(m["sid"]) or mask_light(m["text_src"])
            prev = [mask_light(t) for t in (c.get("prev") or [])]
            nxt = mask_light(c.get("next")) if c.get("next") else None
            rec = {
                "sid": m["sid"],
                "amount": m["amount"],
                "party": m["party"],
                "item": m["item"],
                "text": sentence,
                "prev": prev,
                "next": nxt,
            }
            m["text"] = sentence
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    groups = defaultdict(list)
    by_item = defaultdict(list)
    for m in mentions:
        groups[(m["item"], m["party"])].append(m)
        by_item[m["item"]].append(m)

    parties = ["原廠", "外廠", "不明"]
    items_order = [name for name, _ in ITEM_PATTERNS] + ["不明"]
    table = []
    for item in items_order:
        row = {"item": item, "cells": {}}
        for party in parties:
            xs = [r["amount"] for r in groups.get((item, party), [])]
            sids_u = {r["sid"] for r in groups.get((item, party), [])}
            med, q1, q3 = quartile(xs)
            row["cells"][party] = {
                "n_amount": len(xs),
                "n_sent": len(sids_u),
                "median": med,
                "q1": q1,
                "q3": q3,
            }
        oem = row["cells"]["原廠"]["median"]
        ext = row["cells"]["外廠"]["median"]
        row["oem_ext_ratio"] = round(oem / ext, 2) if oem and ext else None
        examples = []
        for ex in pick_examples(by_item.get(item, [])):
            examples.append({
                "sid": ex["sid"],
                "amount": ex["amount"],
                "party": ex["party"],
                "item": ex["item"],
                "text": ex["text"],
            })
        row["examples"] = examples
        table.append(row)

    summary = {
        "n_aftersales_sentences": n_sent,
        "n_mentions": len(mentions),
        "n_sentences": len({m["sid"] for m in mentions}),
        "note": "論壇口述價格，不是 Lexus 官方定價。",
        "table": table,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sentences {n_sent} mentions {len(mentions)} unique_sid {summary['n_sentences']}")
    print(f"wrote {OUT}")
    for row in table:
        cells = row["cells"]
        print(
            f"{row['item']}\t"
            f"OEM n={cells['原廠']['n_sent']}/{cells['原廠']['n_amount']} med={cells['原廠']['median']}\t"
            f"EXT n={cells['外廠']['n_sent']}/{cells['外廠']['n_amount']} med={cells['外廠']['median']}\t"
            f"UNK med={cells['不明']['median']} n={cells['不明']['n_amount']}\t"
            f"ratio={row['oem_ext_ratio']}"
        )


if __name__ == "__main__":
    main()
