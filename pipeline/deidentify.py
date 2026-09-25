"""PB-02 去識別化：產生簡報／Demo 用語料，不改原始檔。

輸出（data/processed/，不進 repo）：
  aftersales_deid.jsonl
  churn_positives_deid.jsonl
  deid_shop_candidates.tsv
  deid_run.log

salt 只寫 D:\\hf_cache\\deid_salt.txt。
"""
import hashlib
import json
import random
import re
import secrets
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
SALT_PATH = Path(r"D:\hf_cache\deid_salt.txt")
SAMPLE_SEED = 42
SAMPLE_N = 50

# 車型代碼，不是車牌。原始車牌正則會誤殺 RX350／ES300 等。
MODEL_PREFIXES = {
    "RX", "NX", "UX", "ES", "IS", "GS", "LS", "LX", "LM", "LC", "RC", "CT",
    "RZ", "SC", "GX", "HS", "LB", "RA", "BM", "MQ", "GL", "GT",
}
PLATE_WORD = {"VS", "NT", "HP", "KM", "CC", "OK", "AM", "PM", "ID", "NO", "TV", "PC"}

NAME_TITLES = "師傅|老闆|技師|店長|經理|先生|小姐|哥|姐|大大"
NAME_RE = re.compile(rf"([\u4e00-\u9fa5]{{1,3}})({NAME_TITLES})")
NAME_DENY = {
    "原廠", "外廠", "這位", "那位", "一位", "哪位", "各位", "樓", "服務",
    "我們", "你們", "他們", "車廠", "保養", "整個", "大拇", "公司", "店裡",
    "廠裡", "這間", "幾位", "技師", "老闆", "店長", "經理", "師傅",
}

SHOP_SUF = "保養廠|車業|汽車|保修|輪胎|車行"
# 前綴必須落在詞邊界，避免「南港保養廠」被切成「港保養廠」。
SHOP_RE = re.compile(
    r"(?<![A-Za-z0-9\u4e00-\u9fa5])("
    r"[\u4e00-\u9fa5]{2,3}(?:車業|車行|汽車|保養廠)"
    r"|[\u4e00-\u9fa5]{2,4}汽車保養廠"
    r")"
)
BAD_SHOP_CHAR = set(
    "的了一是在有不也都要會能可把被從對為與和或就而但因所這那我你他她們個去到"
    "說問看找換進離開跑給讓叫想知覺得結包其另賣製取希直本後雖印隔關泡約每據"
    "減加先替自協容然各機休反顧遇畢週全召坐妥預順當幾暗最常開代維沒用來下回"
    "做完跟及等很太比才又用外求私訊"
)
BRAND_RE = re.compile(
    r"三菱|標緻|福特|本田|日產|現代|馬自達|賓士|保時捷|福斯|奧迪|寶馬|"
    r"速霸陸|鈴木|裕隆|納智捷|現代|起亞|富豪|積架|特斯拉"
)
OEM_RE = re.compile(
    r"和泰|lexus|exus|toyota|yota|豐田|原廠|南港|濱江|民族|中和|北都|桃苗|"
    r"國都|和運|內湖|敦南|中壢|新店|士林|重慶",
    re.I,
)
GENERIC_RE = re.compile(
    r"民間|外面|外廠|各地|的|在|去|是|如果|因為|但是|所以|二手|中古|進口|"
    r"日本|德國|台灣|臺灣|女生|請|預算|月份|十大|歡迎|竟然|檢查|發現|以及|"
    r"電瓶|煞車|旗艦|豪華|吋|寸|顆|換胎|換輪|這間|很多|當然|基本上|總代理|"
    r"感覺|只有|還有|不過|至於|對輪|我輪|你的|跟輪|右前|現在|除了|已經|"
    r"有四|有推|保固|都體|月後|賣過|可靠|以下|第一|全聯|人對|大家|眼中|"
    r"銷商|過保|紅牌|or汽|H汽|A地|北部|南部|中部|東部|西部|外面|進保|"
    r"去保|但保|原廠|汽車保|保養廠|輪胎"
)
BRAND_TIRE = re.compile(r"橫濱|米其林|普利司通|固特異|馬牌|鄧祿普|固特")

MOBILE_RE = re.compile(r"09\d{2}[-\s]?\d{3}[-\s]?\d{3}")
LAND_RAW_RE = re.compile(r"0\d{1,2}[-\s]?\d{6,8}")
LAND_RE = re.compile(
    r"(?<!\d)(?:0\d{1,2}-\d{6,8}|0\d{1,2}-\d{3,4}-\d{3,4}|0800-?\d{6})(?!\d)"
)
LINE_RAW_RE = re.compile(
    r"(LINE|Line|line|賴)\s*(ID|id|Id)?\s*[:：]?\s*[A-Za-z0-9_.\-]{4,}"
)
LINE_RE = re.compile(
    r"(?:LINE|Line|line)\s*(?:ID|id|Id)\s*[:：]?\s*[A-Za-z0-9_.\-]{4,}"
    r"|賴\s*(?:ID|id|Id)?\s*[:：]\s*[A-Za-z0-9_.\-]{4,}"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://\S+|www\.[A-Za-z0-9.\-]+[^\s\u4e00-\u9fa5]*", re.I)
AT_RE = re.compile(r"(?<![A-Za-z0-9._%+\-])@[A-Za-z0-9_.]{3,}")
PLATE_RAW_RE = re.compile(r"[A-Z]{2,3}[-\s]?\d{3,4}|\d{3,4}[-\s]?[A-Z]{2}")
PLATE_RE = re.compile(r"[A-Z]{2,3}-\d{3,4}|\d{3,4}-[A-Z]{2,3}|[A-Z]{3}\d{4}")
ADDR_RE = re.compile(
    r"([\u4e00-\u9fa5]{1,3})?([縣市區鄉鎮])([\u4e00-\u9fa5]{2,6})"
    r"(路|街|巷|弄|號|段)"
    r"(?:[一二三四五六七八九十\d]{0,4}(?:段|巷|弄|號))?"
    r"(?:\d{1,4}號)?"
)

FUNC_CHARS = set("的了在是去到把被與和或及而就都也會要能可從對為以之等個家間這那我你他她們很不又再但因所")


def load_salt() -> str:
    if SALT_PATH.exists():
        return SALT_PATH.read_text(encoding="utf-8").strip()
    SALT_PATH.parent.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_hex(16)
    SALT_PATH.write_text(salt + "\n", encoding="utf-8")
    return salt


def hid(salt: str, source: str, value: str) -> str:
    raw = f"{salt}{source}{value if value is not None else ''}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def is_model_token(tok: str) -> bool:
    m = re.fullmatch(r"([A-Z]{2,3})[-\s]?(\d{3,4})[Hh]?", tok)
    if m and m.group(1) in MODEL_PREFIXES:
        return True
    m2 = re.fullmatch(r"(\d{3,4})[-\s]?([A-Z]{2})", tok)
    if m2 and m2.group(2) in PLATE_WORD:
        return True
    return False


def shop_decision(name: str, count: int):
    suf = next(s for s in ("保養廠", "車業", "汽車", "保修", "輪胎", "車行") if name.endswith(s))
    pre = name[: -len(suf)]
    if pre in {"汽車", "保養", "車業", "車行", "一般", "民間", "專業", "外面", "小型", "品牌", "優質", "各地", "美國", "日本", "德國", "台灣", "臺灣", "中國", "韓國", "英國", "日野", "台北", "臺北", "台中", "高雄", "新北", "桃園", "台南", "新竹"}:
        return "排除", "通用詞、品牌或地名，不是具體店家"
    if any(ch in BAD_SHOP_CHAR for ch in pre):
        return "排除", "前綴含語句用字，不是店名"
    if not pre or not re.fullmatch(r"[A-Za-z]{1,4}|[\u4e00-\u9fa5]{1,4}", pre):
        return "排除", "前綴不符 1–4 中文或英文"
    if OEM_RE.search(name):
        return "排除", "原廠、Lexus/Toyota、和泰或縣市服務廠／經銷據點"
    if suf == "輪胎" or BRAND_TIRE.search(name):
        return "排除", "輪胎描述或輪胎品牌，不是具體店家"
    if suf == "保修":
        return "排除", "保修多為保固語境，不是店名"
    if BRAND_RE.search(name):
        return "排除", "汽車品牌，不是具體店家"
    if GENERIC_RE.search(pre) or any(ch in FUNC_CHARS for ch in pre):
        return "排除", "通用詞或語句片段，不是具體店家"
    if re.search(r"[A-Za-z]", pre):
        return "排除", "英數碎片（多半是 Lexus/Toyota 被截斷）"
    if suf == "汽車" and len(pre) < 2:
        return "排除", "汽車前綴過短，無法確認是店名"
    if suf in {"車業", "車行", "保養廠", "汽車"}:
        if count >= 2:
            return "納入", "次數 ≥ 2 的具體店家，替換為某外廠"
        return "納入", "補規則：次數為 1 的具體店名仍可識別，一併替換為某外廠"
    return "排除", "未達店家形態"


def scan_shops(rows):
    """詞邊界上的「2–4 字 + 店家後綴」。1 字前綴幾乎都是碎片，不列入。"""
    counts = Counter()
    for row in rows:
        text = f"{row.get('title') or ''}\n{row.get('text') or ''}"
        for m in SHOP_RE.finditer(text):
            counts[m.group(0)] += 1
    return counts


def compile_shop_map(counts: Counter):
    rows = []
    replace = {}
    for name, count in counts.most_common():
        decision, reason = shop_decision(name, count)
        rows.append((name, count, decision, reason))
        if decision == "納入":
            replace[name] = count
    # 長名優先，避免短名先切掉長名
    ordered = sorted(replace, key=len, reverse=True)
    if ordered:
        pat = re.compile("|".join(re.escape(n) for n in ordered))
    else:
        pat = None
    return rows, pat


def mask_address(text: str, counts: Counter) -> str:
    def repl(m):
        counts["地址"] += 1
        city, admin = m.group(1), m.group(2)
        if admin in {"縣", "市"} and city:
            return f"{city}{admin}[地址]"
        # 匹配起點在區／鄉／鎮：往前找縣市
        start = m.start()
        prefix = text[max(0, start - 6) : start + 1]
        city_m = re.search(r"([\u4e00-\u9fa5]{1,3}[縣市])$", prefix)
        if city_m:
            return f"{city_m.group(1)}[地址]"
        return "[地址]"

    return ADDR_RE.sub(repl, text)


def mask_plate(text: str, counts: Counter) -> str:
    counts["車牌_原始正則"] += len(PLATE_RAW_RE.findall(text))

    def repl(m):
        tok = m.group(0)
        if is_model_token(tok):
            counts["車牌_排除車型"] += 1
            return tok
        counts["車牌"] += 1
        return "[車牌]"

    return PLATE_RE.sub(repl, text)


def mask_name(text: str, counts: Counter) -> str:
    def repl(m):
        raw_prefix, title = m.group(1), m.group(2)
        split_at = 0
        for i, ch in enumerate(raw_prefix):
            if ch in FUNC_CHARS or ch in "就算請問原廠這那位樓版層的廠":
                split_at = i + 1
        prefix = raw_prefix[split_at:]
        if not prefix or prefix in NAME_DENY:
            counts["稱謂_排除非人名"] += 1
            return m.group(0)
        if title == "大大" and prefix in {"問", "請", "樓", "層", "版", "這", "那"}:
            return m.group(0)
        counts["人名稱謂"] += 1
        return raw_prefix[:split_at] + "某" + title

    return NAME_RE.sub(repl, text)


def mask_text(text: str, counts: Counter, shop_pat) -> str:
    if not text:
        return text
    counts["手機_原始"] += len(MOBILE_RE.findall(text))
    counts["市話_原始"] += len(LAND_RAW_RE.findall(text))
    counts["LINE_原始"] += len(LINE_RAW_RE.findall(text))

    def subn(pat, repl, s, key):
        s2, n = pat.subn(repl, s)
        counts[key] += n
        return s2

    text = subn(EMAIL_RE, "[email]", text, "Email")
    text = subn(URL_RE, "[網址]", text, "URL")
    text = subn(LINE_RE, "[LINE ID]", text, "LINE ID")
    text = subn(AT_RE, "[帳號]", text, "帳號")
    text = subn(MOBILE_RE, "[電話]", text, "手機")
    text = subn(LAND_RE, "[電話]", text, "市話")
    text = mask_plate(text, counts)
    text = mask_name(text, counts)
    if shop_pat is not None:
        text = subn(shop_pat, "某外廠", text, "店家")
    text = mask_address(text, counts)
    return text


def transform(row, salt, counts, shop_pat):
    out = dict(row)
    source = row.get("source") or ""
    out["author"] = hid(salt, source, row.get("author") or "")
    out["doc_id"] = hid(salt, source, str(row.get("doc_id") or ""))
    out.pop("url", None)
    out["title"] = mask_text(row.get("title") or "", counts, shop_pat)
    out["text"] = mask_text(row.get("text") or "", counts, shop_pat)
    return out


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    salt = load_salt()
    after = list(load_jsonl(DATA / "aftersales.jsonl"))
    pos = list(load_jsonl(DATA / "churn_positives.jsonl"))
    shop_counts = scan_shops(after)
    shop_rows, shop_pat = compile_shop_map(shop_counts)

    tsv = DATA / "deid_shop_candidates.tsv"
    with tsv.open("w", encoding="utf-8", newline="\n") as f:
        f.write("name\tcount\tdecision\treason\n")
        for name, count, decision, reason in shop_rows:
            f.write(f"{name}\t{count}\t{decision}\t{reason}\n")

    counts = Counter()
    after_out = [transform(r, salt, counts, shop_pat) for r in after]
    # 店家詞表只從售後句統計；流失句用同一詞表，但計數分開列在 log
    pos_counts = Counter()
    pos_out = [transform(r, salt, pos_counts, shop_pat) for r in pos]
    # 報告用售後句＋流失句合計（流失句是售後子集，店家掃描不重複計 title 以外）
    # 命中次數以兩份輸出實際替換次數相加，流失句文本多半已含在售後句。
    # 為避免雙重計算，主計數只用 aftersales；流失檔另記。
    write_jsonl(DATA / "aftersales_deid.jsonl", after_out)
    write_jsonl(DATA / "churn_positives_deid.jsonl", pos_out)

    rng = random.Random(SAMPLE_SEED)
    sample = rng.sample(pos_out, SAMPLE_N)
    sample_path = DATA / "deid_sample50.jsonl"
    write_jsonl(sample_path, sample)

    included = [(n, c, d, r) for n, c, d, r in shop_rows if d == "納入"]
    log = DATA / "deid_run.log"
    lines = [
        f"aftersales {len(after)} -> {len(after_out)}",
        f"churn_positives {len(pos)} -> {len(pos_out)}",
        f"salt_reused {SALT_PATH.exists()}",
        f"shops_candidates {len(shop_rows)} included {len(included)}",
        "after_counts " + json.dumps(counts, ensure_ascii=False),
        "pos_counts " + json.dumps(pos_counts, ensure_ascii=False),
        "included " + "、".join(n for n, *_ in included),
    ]
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("--- sample50 ---")
    for i, row in enumerate(sample, 1):
        print(f"{i:02d}\t{row['sid']}\t{row.get('title','')[:40]}\t{row.get('text','')}")


if __name__ == "__main__":
    main()
