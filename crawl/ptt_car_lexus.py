# -*- coding: utf-8 -*-
"""
爬取 PTT car 板標題含 "lexus" 的全部文章（含推文）。
可續跑：已抓過的文章（以 URL 為 key）會跳過。
輸出：
  data/ptt/car_lexus_index.jsonl   搜尋結果索引（每篇一行）
  data/ptt/car_lexus_articles.jsonl 文章全文 + 推文（每篇一行）
  data/ptt/crawl.log
"""
import json, re, sys, time, random, pathlib, datetime
import requests
from bs4 import BeautifulSoup

BOARD = "car"
QUERY = "lexus"
BASE = "https://www.ptt.cc"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "ptt"
OUT.mkdir(parents=True, exist_ok=True)
INDEX = OUT / f"{BOARD}_{QUERY}_index.jsonl"
ARTICLES = OUT / f"{BOARD}_{QUERY}_articles.jsonl"
LOG = OUT / "crawl.log"
DELAY = (0.5, 0.9)

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140 Safari/537.36"
S.cookies.set("over18", "1", domain=".ptt.cc")

def log(msg):
    line = f"{datetime.datetime.now():%H:%M:%S} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def get(url, tries=4):
    for i in range(tries):
        try:
            r = S.get(url, timeout=20)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
            log(f"HTTP {r.status_code} {url} (try {i+1})")
        except requests.RequestException as e:
            log(f"ERR {e} {url} (try {i+1})")
        time.sleep(2 + 2 * i)
    return None

def sleep():
    time.sleep(random.uniform(*DELAY))

# ---------- 1. 搜尋結果索引 ----------
def max_page(html):
    pages = [int(x) for x in re.findall(r"search\?page=(\d+)", html)]
    return max(pages) if pages else 1

def parse_search(html):
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for ent in soup.select("div.r-ent"):
        a = ent.select_one("div.title a")
        if not a:  # 已刪除文章
            continue
        title = a.get_text(strip=True)
        rows.append({
            "url": BASE + a["href"],
            "title": title,
            "is_reply": title.startswith("Re:"),
            "category": (re.match(r"(?:Re: )?\[([^\]]+)\]", title) or [None, None])[1],
            "date_md": ent.select_one("div.date").get_text(strip=True) if ent.select_one("div.date") else None,
            "author": ent.select_one("div.author").get_text(strip=True) if ent.select_one("div.author") else None,
            "push_hint": ent.select_one("div.nrec").get_text(strip=True) if ent.select_one("div.nrec") else "",
        })
    return rows

def build_index():
    if INDEX.exists():
        rows = [json.loads(l) for l in INDEX.open(encoding="utf-8")]
        log(f"索引已存在，{len(rows)} 筆，略過搜尋階段")
        return rows
    first = get(f"{BASE}/bbs/{BOARD}/search?q={QUERY}")
    if not first:
        sys.exit("搜尋首頁抓不到")
    n = max_page(first)
    log(f"搜尋頁共 {n} 頁")
    rows, seen = [], set()
    for p in range(1, n + 1):
        html = first if p == 1 else get(f"{BASE}/bbs/{BOARD}/search?page={p}&q={QUERY}")
        if not html:
            log(f"page {p} 失敗，跳過")
            continue
        for r in parse_search(html):
            if r["url"] not in seen:
                seen.add(r["url"]); rows.append(r)
        if p % 10 == 0:
            log(f"索引進度 {p}/{n}，累計 {len(rows)} 篇")
        sleep()
    with INDEX.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"索引完成：{len(rows)} 篇")
    return rows

# ---------- 2. 文章全文 ----------
def parse_article(url, html):
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("#main-content")
    if not main:
        return None
    meta = {}
    for line in main.select("div.article-metaline, div.article-metaline-right"):
        tag = line.select_one("span.article-meta-tag")
        val = line.select_one("span.article-meta-value")
        if tag and val:
            meta[tag.get_text(strip=True)] = val.get_text(strip=True)
        line.decompose()
    pushes = []
    for p in main.select("div.push"):
        t = p.select_one("span.push-tag"); u = p.select_one("span.push-userid")
        c = p.select_one("span.push-content"); d = p.select_one("span.push-ipdatetime")
        pushes.append({
            "tag": t.get_text(strip=True) if t else "",
            "user": u.get_text(strip=True) if u else "",
            "content": re.sub(r"^:\s?", "", c.get_text()) .strip() if c else "",
            "time": d.get_text(strip=True) if d else "",
        })
        p.decompose()
    for x in main.select("span.f2"):  # ※ 發信站 / 文章網址 / 編輯紀錄
        x.decompose()
    body = main.get_text("\n")
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    # 去掉引用行（"： " 開頭）另存，方便之後只看原創內容
    quoted = [l for l in body.split("\n") if l.startswith(": ")]
    body_no_quote = "\n".join(l for l in body.split("\n") if not l.startswith(": ")).strip()
    return {
        "url": url,
        "aid": url.rsplit("/", 1)[-1].replace(".html", ""),
        "board": BOARD,
        "title": meta.get("標題"),
        "author": meta.get("作者"),
        "time_raw": meta.get("時間"),
        "body": body,
        "body_no_quote": body_no_quote,
        "quoted_lines": len(quoted),
        "pushes": pushes,
        "n_push": sum(1 for p in pushes if p["tag"] == "推"),
        "n_boo": sum(1 for p in pushes if p["tag"] == "噓"),
        "n_arrow": sum(1 for p in pushes if p["tag"] == "→"),
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }

def crawl_articles(index):
    done = set()
    if ARTICLES.exists():
        for l in ARTICLES.open(encoding="utf-8"):
            try:
                done.add(json.loads(l)["url"])
            except Exception:
                pass
    todo = [r for r in index if r["url"] not in done]
    log(f"文章階段：已抓 {len(done)}，待抓 {len(todo)}")
    ok = fail = 0
    with ARTICLES.open("a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            html = get(r["url"])
            art = parse_article(r["url"], html) if html else None
            if art:
                art["index_title"] = r["title"]; art["category"] = r["category"]; art["is_reply"] = r["is_reply"]
                f.write(json.dumps(art, ensure_ascii=False) + "\n"); f.flush(); ok += 1
            else:
                fail += 1; log(f"失敗：{r['url']}")
            if i % 50 == 0:
                log(f"文章進度 {i}/{len(todo)}（成功 {ok}，失敗 {fail}）")
            sleep()
    log(f"文章完成：成功 {ok}，失敗 {fail}，總計檔內 {len(done) + ok} 篇")

if __name__ == "__main__":
    log("=== 開始 ===")
    idx = build_index()
    crawl_articles(idx)
    log("=== 結束 ===")
