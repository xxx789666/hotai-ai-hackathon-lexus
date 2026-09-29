# -*- coding: utf-8 -*-
"""L6：四個 Persona × 三個接觸點，各生成一則 Lexus 售後訊息。

檢索用字元 bigram 的 TF-IDF（知識庫 jsonl，條目 id 對齊 md 的 1..72）。
生成只呼叫 cursor-agent 的 gpt-5.6-sol-high，prompt 從 stdin 進入。
事實查核與重生成在 factcheck_messages.py。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / "knowledge" / "lexus_aftersales_kb.jsonl"
OUT = ROOT / "data" / "processed" / "generated_messages.jsonl"
LOG_DIR = ROOT / "data" / "processed" / "llm_logs"
CURSOR_AGENT = r"C:\Users\xx\AppData\Local\cursor-agent\cursor-agent.cmd"
MODEL = "gpt-5.6-sol-high"

# 官網寫明未公開、或只是抓取說明的條目，不能當事實來源。
SKIP_IDS = {"36", "37", "38", "39", "40"}
# 點數與會員禮遇數字多，和這三個接觸點無關，避免 1.5%、折扣被誤引用。
SKIP_IDS |= {"29", "30", "66", "67"}

BANNED = (
    "車麗屋", "好市多", "愛馬龍", "殺肉", "潭子", "論壇", "Mobile01", "PTT", "Dcard",
    "否則", "最後機會", "趕緊", "務必把握", "保證修好", "一定能查出", "一定修好",
    "過保精算派", "品質失望派", "口碑建議者", "靜默出走者",
    "我們知道", "外廠比較", "1.5 倍", "1.5倍", "60 天", "60天",
)


def char_len(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def fold_digits(text: str) -> str:
    text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    return re.sub(r"(?<=\d)[,，](?=\d)", "", text)


def extract_numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", fold_digits(text))


def numbers_missing(text: str, corpus: str) -> list[str]:
    corpus_f = fold_digits(corpus)
    missing = []
    for num in extract_numbers(text):
        if not re.search(rf"(?<!\d){re.escape(num)}(?!\d)", corpus_f):
            missing.append(num)
    return missing


def cjk_bigrams(text: str) -> list[str]:
    grams = []
    buf = []

    def flush():
        if len(buf) >= 2:
            s = "".join(buf)
            grams.extend(s[i:i + 2] for i in range(len(s) - 1))
        elif len(buf) == 1:
            grams.append(buf[0])
        buf.clear()

    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            buf.append(ch)
        else:
            flush()
            if ch.isdigit():
                grams.append(ch)
    flush()
    return grams


def load_kb() -> list[dict]:
    rows = []
    for i, line in enumerate(KB_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["id"] = str(i)
        rows.append(row)
    return rows


def index_kb(rows: list[dict]):
    docs = []
    df = Counter()
    for row in rows:
        if row["id"] in SKIP_IDS:
            continue
        blob = f"{row['topic']} {row['topic']} {row['topic']} {row['text']}"
        tf = Counter(cjk_bigrams(blob))
        docs.append((row, tf))
        df.update(tf.keys())
    n = len(docs)
    idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
    vecs = []
    for row, tf in docs:
        weight = {t: c * idf.get(t, 0.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in weight.values())) or 1.0
        vecs.append((row, weight, norm))
    return vecs, idf


def retrieve(query: str, vecs, idf, k: int = 5) -> list[dict]:
    """TF-IDF 餘弦，再加上查詢片語是否出現在主題或正文的加分。片語用 | 分開。"""
    phrases = [p.strip() for p in query.split("|") if p.strip()]
    qtf = Counter(cjk_bigrams(query.replace("|", "")))
    qweight = {t: c * idf.get(t, 0.0) for t, c in qtf.items()}
    qnorm = math.sqrt(sum(v * v for v in qweight.values())) or 1.0
    scored = []
    for row, weight, norm in vecs:
        dot = sum(qweight.get(t, 0.0) * weight.get(t, 0.0) for t in qweight)
        bonus = 0.0
        blob = row["topic"] + " " + row["text"]
        for phrase in phrases:
            if len(phrase) < 2:
                continue
            if phrase in row["topic"]:
                bonus += 0.45
            elif phrase in blob:
                bonus += 0.18
        if "電池" not in query and ("電池" in row["topic"] or row["topic"].startswith("BEV")):
            bonus -= 0.8
        scored.append((dot / (qnorm * norm) + bonus, row))
    scored.sort(key=lambda x: (-x[0], int(x[1]["id"])))
    out = []
    for score, row in scored[:k]:
        item = dict(row)
        item["score"] = round(score, 4)
        out.append(item)
    return out


PERSONAS = [
    {
        "name": "過保精算派",
        "definition": (
            "高／中風險作者 511 人（39.9%）。句子近半在談價格，替代出路是一般外廠與自備料。"
            "至少一句過保的人占 15.7%，平均風險 0.73，四組裡最高。他們要算得清楚的官方數字。"
        ),
        "quotes": [
            "去外面換就好，原廠換很貴，外面四顆全換12000有找",
            "我記得原廠一顆換下來要6、7千，可以去車麗屋或是好市多換會比較省",
            "過保固的話，可以找殺肉件，不過大燈的價格不菲，LS600h頭燈應該是LED頭燈，價格更高。",
        ],
    },
    {
        "name": "品質失望派",
        "definition": (
            "247 人（19.3%）。技術品質占句子 43%，價格 15%。替代裡看得到他牌或換車。"
            "痛點是原廠查不出、處理不好，不是先被價格說服。"
        ),
        "quotes": [
            "有回原廠看過但查不出來，但原廠技師懷疑可能是底盤問題，要我再將車多留幾天查，想問是否有台中外廠維修推薦",
            "原廠處理不好就去外場",
            "已預約北部服務廠4月底把車送上去留車請他們處理台中潭子廠處理不來的問題",
        ],
    },
    {
        "name": "口碑建議者",
        "definition": (
            "195 人（15.2%）。立場是建議他人的句子占 61%，會把別的車主一起帶走。"
            "他們轉述的往往是電瓶、輪胎不必留在原廠。訊息要給可以轉述的官方保證，而不是反駁他。"
        ),
        "quotes": [
            "去車麗屋或輪胎行他們有手持可看哪輪沒讀數，如沒電就全換。",
            "還有電瓶外面換就可以了，愛馬龍便宜耐用",
            "去外廠 一顆一顆慢慢換就好",
        ],
    },
    {
        "name": "靜默出走者",
        "definition": (
            "128 人（10.0%）。這些代表句沒有負面抱怨，替代有 55% 是一般外廠。"
            "人是安靜地在找別的廠。不要點破，也不要打電話追。給一個低壓力的官方回廠方式。"
        ),
        "quotes": [
            "請問北部有推薦 LEXUE ES240 拉基棒維修的地方嗎?",
            "我的NX200t 音響完全沒有聲音了, 請問除了原廠, 台北可以去哪修?",
            "有沒有推薦比較專業車廠(台中市）",
        ],
    },
]

TOUCHPOINTS = [
    {
        "id": "T1",
        "label": "保固到期前 60 天",
        "situation": (
            "CRM 保固到期日在 60 天內。60 是內部規則，正文不要寫天數。"
            "用「保固即將屆滿」帶出仍可核對的新車基本保證，以及準時定保的免費延長保證資格。"
            "不要催購延保，不要逐車系報價。"
        ),
    },
    {
        "id": "T2",
        "label": "回廠間隔拉長",
        "situation": (
            "距上次定保已超過建議週期的 1.5 倍。1.5 是內部規則，正文不要寫。"
            "請用知識庫裡的保養週期說法（半年、一萬公里、六個月）邀請回廠，"
            "可以連到準時定保與免費延長保證的資格條件。不要寫定保價格。"
        ),
    },
    {
        "id": "T3",
        "label": "刪項後首次回廠",
        "situation": (
            "上次工單有車主未同意的估價項目，或有自備料註記。這是刪項之後第一次聯繫。"
            "說明自費更換的正廠零件保證，以及自備油品、消耗性零件不在保證內。"
            "不要猜測被刪的是哪一個零件，不要報價，不要寫定保價格。"
        ),
    },
]

# (persona, touchpoint) -> channel, kpi, 檢索用語, 渠道寫法
GRID = {
    ("過保精算派", "T1"): (
        "Email", "點擊",
        "新車基本保證|120,000|免費延長保證|6 個月|8 次|14 萬|69,000|定保套餐",
        "Email：以「您好」起首，一段把資格說完，結尾請對方點選預約。不要寫網址。",
    ),
    ("過保精算派", "T2"): (
        "LINE 官方帳號推播", "預約",
        "每一萬公里|每半年|每六個月|6 個月|8 次|免費延長保證|定保套餐|原廠機油",
        "LINE 官方帳號：兩小段，先講週期，再講準時定保和延長保證的關係。不要表情符號。",
    ),
    ("過保精算派", "T3"): (
        "服務廠專員電話腳本", "預約",
        "正廠零件|50,000|自備油品|消耗性零件|2 年|定保套餐",
        "電話腳本：服務廠專員第一人稱，直接對車主說。不要舞台指示、不要括號。",
    ),
    ("品質失望派", "T1"): (
        "服務廠專員電話腳本", "預約",
        "新車基本保證|120,000|尊榮安檢|25 項|全年免費|免費延長保證|6 個月",
        "電話腳本：先承認保固窗口還在，再約一次安檢。不要承諾能查出上次的問題。",
    ),
    ("品質失望派", "T2"): (
        "App 通知", "點擊",
        "尊榮安檢|25 項|全年免費|每一萬公里|每半年|隨時回廠",
        "App 通知：先講一件官方服務（尊榮安檢），再一個點開預約的動作。不要長篇。",
    ),
    ("品質失望派", "T3"): (
        "服務廠專員電話腳本", "回廠",
        "尊榮安檢|25 項|全年免費|正廠零件|50,000|消耗性零件|自備油品",
        "電話腳本：把上次未做的項目留成車主的決定。只說明零件保證與安檢，不施壓。",
    ),
    ("口碑建議者", "T1"): (
        "LINE 官方帳號推播", "點擊",
        "新車基本保證|120,000|電瓶保證|輪胎保證|免費延長保證|半年|第 5 年",
        "LINE：寫成他可以轉述給車友的官方說法，不要反駁「去外面換」。不要表情符號。",
    ),
    ("口碑建議者", "T2"): (
        "Email", "點擊",
        "電瓶保證|輪胎保證|18 個月|30,000|50,000|正廠零件|每半年|原廠機油",
        "Email：一段，把電瓶或輪胎的官方保證與保養週期寫成可轉寄的說明。不要報價。",
    ),
    ("口碑建議者", "T3"): (
        "App 通知", "預約",
        "正廠零件|50,000|18 個月|30,000|輪胎保證|自備油品|消耗性零件",
        "App 通知：提醒自備料與正廠零件保證的差別，邀請預約由專人對一次保養紀錄。",
    ),
    ("靜默出走者", "T1"): (
        "App 通知", "點擊",
        "新車基本保證|120,000|20 分鐘|1 天|免費延長保證|第 5 年|半年",
        "App 通知：低壓力。告知保固即將屆滿與 App 預約方式，不要問他是不是在找別的廠。",
    ),
    ("靜默出走者", "T2"): (
        "LINE 官方帳號推播", "預約",
        "20 分鐘|1 天|尊榮安檢|25 項|全年免費|每半年|每一萬公里",
        "LINE：只邀請依週期回廠或做免費安檢。不要提外廠，不要表情符號。",
    ),
    ("靜默出走者", "T3"): (
        "Email", "點擊",
        "20 分鐘|1 天|正廠零件|50,000|自備油品|消耗性零件",
        "Email：書面、可稍後再看。說明零件保證與預約保留時間，把決定權留下。",
    ),
}


def cells() -> list[dict]:
    out = []
    for persona in PERSONAS:
        for tp in TOUCHPOINTS:
            channel, kpi, query, style = GRID[(persona["name"], tp["id"])]
            out.append({
                "persona": persona["name"],
                "definition": persona["definition"],
                "quotes": persona["quotes"],
                "touchpoint": tp["id"],
                "touchpoint_label": tp["label"],
                "situation": tp["situation"],
                "channel": channel,
                "kpi": kpi,
                "query": query,
                "channel_style": style,
            })
    return out


def clip(text: str, limit: int = 1400) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def build_prompt(cell: dict, hits: list[dict], feedback: str | None) -> str:
    entries = []
    for hit in hits:
        entries.append(f"[id={hit['id']}] {hit['topic']}\n{clip(hit['text'])}")
    quotes = "\n".join(f"- {q}" for q in cell["quotes"])
    extra = ""
    if feedback:
        extra = (
            "\n上次這格沒有通過，請整則重寫，不要沿用上次的句子。\n"
            f"未通過原因：\n{feedback}\n"
        )
    return f"""你是 Lexus 台灣售後的內容編輯。依下面這一格寫一則給車主的訊息。
不要讀取檔案，不要使用工具。只輸出一個 JSON 物件，第一個字元必須是 {{ 。
不要 markdown，不要前言。

JSON 欄位：
- text：給車主的正文。繁體中文，80 到 150 字（空白不算）。至少包含一個可用條目裡的阿拉伯數字，且每個阿拉伯數字都要在你引用的條目原文裡以相同數字出現。
- cited_ids：字串陣列，至少 1 個，只能填下面可用條目的 id。
- design_note：一句，40 字以內，說明這則怎麼對準此 Persona 的痛點。這句不給車主看。
- kpi：必須正好是「{cell['kpi']}」。

禁止：
- 不要出現論壇、帳號、真名，也不要抄代表句的店名、地名、車型、口述價格。
- 不要寫定保或單次保養的價格（官網未公開）。金額最多出現一次，禁止逐車系報價，禁止寫折扣。
- 不要寫「60天」「1.5倍」或任何條目裡沒有的數字。
- 不要推銷、不要威脅。不要用「否則」「最後機會」「趕緊」「務必把握」。
- 資格條件用平述：準時與否會影響免費延長保證，說完即可。
- 不要承諾條目沒寫的事，尤其不要保證查出故障、不要說消耗零件免費更換、不要說定保全免費。
- 不要寫「我們知道您在比較」。
- 語氣克制，決定權留給車主。數字用阿拉伯數字，照條目抄，不要換算、不要改成國字。

Persona：{cell['persona']}
定義：{cell['definition']}
代表句只供理解痛點，一個字都不要抄進 text：
{quotes}

接觸點：{cell['touchpoint_label']}
情境：{cell['situation']}
渠道：{cell['channel']}
{cell['channel_style']}
期望 KPI：{cell['kpi']}

可用條目：
{chr(10).join(entries)}
{extra}"""


def extract_json(text: str) -> dict:
    decoder = json.JSONDecoder()
    found = []
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            found.append(obj)
    if not found:
        raise ValueError(f"no JSON: {text[:300]}")
    for obj in reversed(found):
        if "text" in obj or "claims" in obj:
            return obj
    return found[-1]


def call_llm(prompt: str, tag: str) -> dict:
    cmd = [CURSOR_AGENT, "-p", "--model", MODEL, "--output-format", "text", "--mode", "ask", "--trust"]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    last_err = "no output"
    for attempt in range(2):
        try:
            res = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
                shell=sys.platform == "win32",
            )
        except subprocess.TimeoutExpired as exc:
            last_err = f"timeout: {exc}"
            continue
        raw = res.stdout or ""
        err = (res.stderr or "")[:500]
        (LOG_DIR / f"{tag}-{attempt}.txt").write_text(raw + "\n---\n" + err, encoding="utf-8")
        if res.returncode != 0 and "{" not in raw:
            last_err = f"exit {res.returncode}: {err}"
            continue
        try:
            return extract_json(raw)
        except ValueError as exc:
            last_err = str(exc)
    raise RuntimeError(last_err)


def norm_id(value) -> str:
    s = str(value).strip()
    s = re.sub(r"(?i)^kb[-_\s]?", "", s)
    if re.fullmatch(r"\d+", s):
        return str(int(s))
    return s


def local_errors(text: str, cited_ids: list[str], hits: list[dict], kpi: str, expect_kpi: str) -> list[str]:
    errors = []
    n = char_len(text)
    if not 80 <= n <= 150:
        errors.append(f"字數 {n}，要 80–150（空白不算）")
    allowed = {h["id"] for h in hits}
    if not cited_ids:
        errors.append("cited_ids 是空的")
    else:
        bad = [i for i in cited_ids if i not in allowed]
        if bad:
            errors.append(f"引用了不在本次檢索結果的 id：{', '.join(bad)}")
    by_id = {h["id"]: h["text"] for h in hits}
    corpus = "\n".join(by_id[i] for i in cited_ids if i in by_id)
    missing = numbers_missing(text, corpus) if corpus else extract_numbers(text)
    if missing:
        errors.append("這些數字不在所引用條目原文：" + "、".join(missing))
    if not extract_numbers(text):
        errors.append("正文沒有任何阿拉伯數字，無法對到知識庫")
    for word in BANNED:
        if word in text:
            errors.append(f"出現禁用詞：{word}")
    if "折" in text:
        errors.append("不要寫折扣")
    money = re.findall(r"\d[\d,]*\s*元", text)
    if len(money) > 1:
        errors.append("金額出現超過一次")
    if re.search(r"定保[^。]{0,12}\d", text) and "元" in text:
        errors.append("疑似寫了定保價格")
    if kpi != expect_kpi:
        errors.append(f"kpi 應為{expect_kpi}，模型寫了{kpi}")
    return errors


def generate_cell(cell: dict, kb_index, feedback: str | None = None, attempt: int = 1) -> dict:
    vecs, idf = kb_index
    hits = retrieve(cell["query"], vecs, idf, 5)
    prompt = build_prompt(cell, hits, feedback)
    tag = f"{cell['persona']}-{cell['touchpoint']}-a{attempt}"
    obj = call_llm(prompt, tag)
    text = re.sub(r"\s+", " ", str(obj.get("text") or "")).strip()
    cited = [norm_id(x) for x in (obj.get("cited_ids") or [])]
    cited = list(dict.fromkeys(cited))
    note = re.sub(r"\s+", " ", str(obj.get("design_note") or "")).strip()
    kpi = str(obj.get("kpi") or "").strip()
    errors = local_errors(text, cited, hits, kpi, cell["kpi"])
    return {
        "persona": cell["persona"],
        "touchpoint": cell["touchpoint"],
        "touchpoint_label": cell["touchpoint_label"],
        "channel": cell["channel"],
        "text": text,
        "cited_ids": cited,
        "design_note": note,
        "kpi": cell["kpi"] if kpi != cell["kpi"] else kpi,
        "attempt": attempt,
        "retrieved_ids": [h["id"] for h in hits],
        "retrieval": [{"id": h["id"], "topic": h["topic"], "score": h["score"]} for h in hits],
        "local_errors": errors,
        "model": MODEL,
    }


def write_jsonl(rows: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieve-only", action="store_true")
    ap.add_argument("--only", default="", help="例如 過保精算派:T1")
    args = ap.parse_args()
    rows = load_kb()
    kb_index = index_kb(rows)
    chosen = cells()
    if args.only:
        name, tp = args.only.split(":")
        chosen = [c for c in chosen if c["persona"] == name and c["touchpoint"] == tp]
    if args.retrieve_only:
        for cell in chosen:
            hits = retrieve(cell["query"], kb_index[0], kb_index[1], 5)
            tops = " | ".join(f"{h['id']}:{h['topic']}:{h['score']}" for h in hits)
            print(f"{cell['persona']} {cell['touchpoint']} {cell['channel']} -> {tops}", flush=True)
        return
    results = []
    for cell in chosen:
        rec = generate_cell(cell, kb_index, attempt=1)
        results.append(rec)
        print(
            f"{rec['persona']} {rec['touchpoint']} chars={char_len(rec['text'])} "
            f"cited={rec['cited_ids']} errors={rec['local_errors']}",
            flush=True,
        )
    if not args.only:
        write_jsonl(results)
    else:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
