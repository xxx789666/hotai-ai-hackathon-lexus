"""三站合併 → 看板/分類過濾 → 切句 → 去重 → 售後關鍵詞篩選。

輸出（data/processed/）：
  sentences.jsonl   全部保留句（已去重）
  aftersales.jsonl  含售後詞的句子（LLM 粗標的輸入）
  stats.json        各階段計數
"""
import json
import re
import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"

MIN_LEN, MAX_LEN = 6, 200

# ---------- 過濾規則 ----------
DCARD_KEEP_FORUMS = {"car", "vehicle", "talk", "trending", "money", "creditcard", "second_hand"}
PTT_DROP_CATS = {"新聞", "菜單", "情報", "徵文", "轉錄", "轉載"}
M01_DROP_TITLE = re.compile(r"試駕|試乘|抽豪禮|抽獎|募集|【採訪】|【新聞】|發表會|上市")
DCARD_DROP_TITLE = re.compile(r"菜單|報價|徵才|誠徵|(?<!售後)出售|代售|認證中古車推薦")

# 售後相關詞：保養維修、費用、保固、服務廠/外廠、零件、召回、服務態度
AFTERSALES = re.compile(
    r"保養|定保|維修|修車|修理|原廠|正廠|副廠|外廠|保修廠|車廠|服務廠|回廠|進廠|廠裡|廠長|"
    r"保固|延保|出保|召回|技師|師傅|服務專員|接待|工資|工錢|零件|料件|機油|煞車|輪胎|電瓶|"
    r"鈑金|烤漆|異音|異響|故障|檢修|檢查|報價單|維修費|保養費|太貴|很貴|坑|被當盤|盤子|"
    r"售後|服務態度|客服|客訴|申訴|和泰|總代理|據點|預約|等料|換車|賣掉|脫手|轉投|換牌"
)

URL_RE = re.compile(r"https?://\S+")
SPLIT_RE = re.compile(r"(?<=[。！？!?；;])|\n+")
NORM_RE = re.compile(r"[\s\W_]+", re.UNICODE)


def clean(text: str) -> str:
    text = URL_RE.sub("", text or "")
    text = re.sub(r"^(B\d+|b\d+)\s*", "", text)          # Dcard 回覆樓層前綴
    text = re.sub(r"[ \t　]+", " ", text)
    return text.strip()


def split_sentences(text: str):
    for chunk in SPLIT_RE.split(clean(text)):
        chunk = chunk.strip(" ，,、~～")
        if not chunk:
            continue
        # 超長句再用逗號切成 ≤ MAX_LEN 的片段
        if len(chunk) > MAX_LEN:
            buf = ""
            for part in re.split(r"(?<=[，,])", chunk):
                if len(buf) + len(part) > MAX_LEN and buf:
                    yield buf
                    buf = ""
                buf += part
            if buf:
                yield buf
        else:
            yield chunk


def ptt_body(body: str) -> str:
    # 去掉簽名檔（最後一個 "\n--" 之後）與引言行
    idx = body.rfind("\n--")
    if idx != -1:
        body = body[:idx]
    return "\n".join(l for l in body.splitlines() if not l.startswith((":", "※", "◆")))


def ptt_time(raw):
    try:
        return datetime.strptime(raw, "%a %b %d %H:%M:%S %Y").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


# ---------- 各站 → 統一單元（unit = 一段正文 / 一則留言） ----------
def units_ptt(stats):
    arts = load(ROOT / "data/ptt/car_lexus_articles.jsonl")
    stats["ptt_docs_raw"] = len(arts)
    kept = [a for a in arts if a.get("category") not in PTT_DROP_CATS and a.get("title")]
    stats["ptt_docs_kept"] = len(kept)
    for a in kept:
        base = dict(source="ptt", board=a["board"], doc_id=a["aid"], url=a["url"],
                    title=a["title"], date=ptt_time(a.get("time_raw")))
        yield {**base, "role": "body", "author": (a.get("author") or "").split(" ")[0],
               "text": ptt_body(a.get("body_no_quote") or a.get("body") or "")}
        # 同一使用者連續推文合併（PTT 長留言會被拆成多行）
        merged = []
        for p in a.get("pushes", []):
            if merged and merged[-1]["user"] == p["user"]:
                merged[-1]["content"] += p["content"]
            else:
                merged.append(dict(p))
        for p in merged:
            yield {**base, "role": "comment", "author": p["user"], "text": p["content"]}


def units_m01(stats):
    topics = load(ROOT / "data/mobile01/lexus_topics.jsonl")
    stats["m01_docs_raw"] = len(topics)
    kept = [t for t in topics if not t.get("pinned") and not M01_DROP_TITLE.search(t["title"])]
    stats["m01_docs_kept"] = len(kept)
    for t in kept:
        base = dict(source="mobile01", board="lexus", doc_id=str(t["t"]), url=t["url"], title=t["title"])
        for p in t["posts"]:
            yield {**base, "date": (p.get("time") or t.get("created") or "")[:10] or None,
                   "role": "body" if p.get("is_op") else "comment",
                   "author": p.get("author"), "text": p.get("text", "")}


def units_dcard(stats):
    posts = load(ROOT / "data/dcard/lexus_posts.jsonl")
    stats["dcard_docs_raw"] = len(posts)
    kept = [p for p in posts if p["forum"] in DCARD_KEEP_FORUMS and not DCARD_DROP_TITLE.search(p["title"])]
    stats["dcard_docs_kept"] = len(kept)
    for p in kept:
        base = dict(source="dcard", board=p["forum"], doc_id=str(p["id"]), url=p["url"], title=p["title"])
        yield {**base, "date": p["createdAt"][:10], "role": "body", "author": p.get("school"),
               "text": p.get("content", "")}
        for c in p.get("comments", []):
            if c.get("hidden"):
                continue
            yield {**base, "date": (c.get("createdAt") or "")[:10] or None, "role": "comment",
                   "author": c.get("school"), "text": c.get("content", "")}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stats = Counter()
    seen = set()
    n_after = 0
    with open(OUT / "sentences.jsonl", "w", encoding="utf-8") as fs, \
         open(OUT / "aftersales.jsonl", "w", encoding="utf-8") as fa:
        for gen in (units_ptt, units_m01, units_dcard):
            for u in gen(stats):
                text = u.pop("text")
                for i, s in enumerate(split_sentences(text)):
                    stats["sent_split"] += 1
                    stats[f"{u['source']}_sent_split"] += 1
                    if len(s) < MIN_LEN:
                        stats["drop_short"] += 1
                        continue
                    key = hashlib.md5(NORM_RE.sub("", s).lower().encode()).hexdigest()
                    if key in seen:
                        stats["drop_dup"] += 1
                        continue
                    seen.add(key)
                    rec = {"sid": f"{u['source'][0]}-{key[:12]}", **u, "pos": i, "text": s}
                    fs.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    stats["sent_kept"] += 1
                    stats[f"{u['source']}_sent_kept"] += 1
                    if AFTERSALES.search(s):
                        fa.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        n_after += 1
                        stats[f"{u['source']}_aftersales"] += 1
    stats["aftersales"] = n_after
    stats["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
