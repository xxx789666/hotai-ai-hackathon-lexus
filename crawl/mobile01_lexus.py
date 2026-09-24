# -*- coding: utf-8 -*-
"""
爬取 Mobile01 LEXUS 版（f=346）全部主題與回覆。
Mobile01 直連 403，本程式透過 web-access CDP proxy（127.0.0.1:3456）在使用者 Chrome 分頁內 fetch，
HTML 回傳本機用 BeautifulSoup 解析。可續跑：已完成的主題（以 t id 為 key）會跳過。
輸出：
  data/mobile01/lexus_topics_index.jsonl  版列表索引
  data/mobile01/lexus_topics.jsonl        每主題一行：meta + posts[]
  data/mobile01/crawl.log
"""
import json, re, sys, time, random, pathlib, datetime
import requests
from bs4 import BeautifulSoup

FORUM = 346
PROXY = "http://127.0.0.1:3456"
SITE = "https://www.mobile01.com"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "mobile01"
OUT.mkdir(parents=True, exist_ok=True)
INDEX = OUT / "lexus_topics_index.jsonl"
TOPICS = OUT / "lexus_topics.jsonl"
LOG = OUT / "crawl.log"
import os
DELAY = tuple(float(x) for x in os.environ.get("M01_DELAY", "1.0,1.5").split(","))  # 秒；長主題連續抓建議 2.5,4.0
TAB_FILE = OUT / "tab_id.txt"


def log(msg):
    line = f"{datetime.datetime.now():%H:%M:%S} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------- CDP proxy ----------
_tab = None


def tab():
    global _tab
    if _tab:
        return _tab
    if TAB_FILE.exists():
        t = TAB_FILE.read_text().strip()
        try:
            r = requests.get(f"{PROXY}/info", params={"target": t}, timeout=10).json()
            if "error" not in r:
                _tab = t
                return _tab
        except Exception:
            pass
    r = requests.get(f"{PROXY}/new", params={"url": f"{SITE}/topiclist.php?f={FORUM}"}, timeout=60).json()
    _tab = r["targetId"]
    TAB_FILE.write_text(_tab)
    time.sleep(4)
    log(f"新開分頁 {_tab}")
    return _tab


def fetch(path, tries=4):
    """在頁面內 fetch 同源路徑，回傳 HTML 字串。"""
    global _tab
    js = ('(async()=>{try{const r=await fetch(%s,{credentials:"include"});'
          'const h=await r.text();return JSON.stringify({s:r.status,h});}'
          'catch(e){return JSON.stringify({s:-1,e:String(e)});}})()') % json.dumps(path)
    for i in range(tries):
        try:
            resp = requests.post(f"{PROXY}/eval", params={"target": tab()}, data=js.encode("utf-8"), timeout=60)
            j = resp.json()
            if "error" in j:
                log(f"eval error {j['error']} (try {i+1})")
                _tab = None  # 分頁可能被關，重開
                time.sleep(3)
                continue
            v = json.loads(j["value"]) if isinstance(j["value"], str) else j["value"]
            h = v.get("h", "")
            if v.get("s") == 200 and ("l-listTable" in h or "l-articlePage" in h):
                return h
            log(f"HTTP {v.get('s')} / 內容異常 {path} (try {i+1})，退避 30s")
            time.sleep(30 + 30 * i)
        except Exception as e:
            log(f"ERR {e} {path} (try {i+1})")
            time.sleep(5)
    return None


def sleep():
    time.sleep(random.uniform(*DELAY))


# ---------- 1. 版列表 ----------
def parse_list(html):
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for tr in soup.select("div.l-listTable__tr"):
        a = tr.select_one("div.c-listTableTd__title a[href*='topicdetail']")
        if not a:
            continue
        m = re.search(r"t=(\d+)", a["href"])
        if not m:
            continue
        names = [x.get_text(strip=True) for x in tr.select("div.l-listTable__td--time a")]
        notes = [x.get_text(strip=True) for x in tr.select("div.l-listTable__td--time .o-fNotes")]
        cnt = tr.select_one("div.l-listTable__td--count")
        jump = [int(x.get_text(strip=True)) for x in tr.select("ul.l-jumpList a") if x.get_text(strip=True).isdigit()]
        rows.append({
            "t": int(m.group(1)),
            "title": a.get_text(strip=True),
            "pinned": "置頂" in tr.get_text(),
            "author": names[0] if names else None,
            "created": notes[0] if notes else None,
            "last_reply_by": names[1] if len(names) > 1 else None,
            "last_reply_at": notes[1] if len(notes) > 1 else None,
            "reply_count": int(cnt.get_text(strip=True)) if cnt and cnt.get_text(strip=True).isdigit() else None,
            "pages_hint": max(jump) if jump else 1,
        })
    pages = [int(x) for x in re.findall(r"f=%d&(?:amp;)?p=(\d+)" % FORUM, html)]
    return rows, (max(pages) if pages else 1)


def build_index():
    if INDEX.exists():
        rows = [json.loads(l) for l in INDEX.open(encoding="utf-8")]
        log(f"索引已存在，{len(rows)} 筆，略過列表階段")
        return rows
    html = fetch(f"/topiclist.php?f={FORUM}")
    if not html:
        sys.exit("列表首頁抓不到")
    rows, n = parse_list(html)
    log(f"版列表共 {n} 頁")
    seen = {r["t"] for r in rows}
    for p in range(2, n + 1):
        sleep()
        h = fetch(f"/topiclist.php?f={FORUM}&p={p}")
        if not h:
            log(f"列表 p{p} 失敗，跳過")
            continue
        rs, _ = parse_list(h)
        for r in rs:
            if r["t"] not in seen:
                seen.add(r["t"])
                rows.append(r)
        if p % 10 == 0:
            log(f"列表進度 {p}/{n}，累計 {len(rows)} 主題")
    with INDEX.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"索引完成：{len(rows)} 主題")
    return rows


# ---------- 2. 主題內容 ----------
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}")


def parse_topic_page(html):
    soup = BeautifulSoup(html, "lxml")
    posts = []
    for blk in soup.select("div.l-articlePage"):
        aid = blk.select_one("a[id^=name_]")
        author = blk.select_one(".c-authorInfo__id")
        body = blk.select_one("[itemprop=articleBody]") or blk.select_one("article")
        if not body:
            continue
        for q in body.select("blockquote"):
            q.replace_with("[引用略]")
        for x in body.select("script,style"):
            x.decompose()
        text = re.sub(r"\n{3,}", "\n\n", body.get_text("\n")).strip()
        blk_text = blk.get_text(" ")
        d = DATE_RE.search(blk_text)
        fl = re.search(r"#(\d+)", blk_text)
        posts.append({
            "post_id": int(aid["id"].split("_")[1]) if aid else None,
            "author": author.get_text(strip=True) if author else None,
            "is_op": "樓主" in blk_text[:2000],
            "floor": int(fl.group(1)) if fl else None,
            "time": d.group(0) if d else None,
            "text": text,
            "n_img": len(body.select("img")),
        })
    pages = [int(x) for x in re.findall(r'data-page="(\d+)"', html)]
    return posts, (max(pages) if pages else 1)


def crawl_topics(index):
    done = set()
    if TOPICS.exists():
        for l in TOPICS.open(encoding="utf-8"):
            try:
                done.add(json.loads(l)["t"])
            except Exception:
                pass
    todo = [r for r in index if r["t"] not in done]
    log(f"主題階段：已抓 {len(done)}，待抓 {len(todo)}")
    ok = fail = fetched = 0
    with TOPICS.open("a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            t = r["t"]
            h = fetch(f"/topicdetail.php?f={FORUM}&t={t}")
            fetched += 1
            if not h:
                fail += 1
                log(f"失敗：t={t}")
                continue
            posts, n = parse_topic_page(h)
            m = re.search(r"<title>([^<]*)</title>", h)
            title = m.group(1).strip() if m else r["title"]
            # 分頁元件只顯示一段視窗，須邊抓邊更新最大頁碼；列表的 pages_hint 也納入
            n = max(n, r.get("pages_hint") or 1)
            seen_ids = {p["post_id"] for p in posts if p["post_id"]}
            p = 2
            while p <= n:
                sleep()
                hp = fetch(f"/topicdetail.php?f={FORUM}&t={t}&p={p}")
                fetched += 1
                if not hp:
                    log(f"t={t} p{p} 失敗，略過該頁")
                    p += 1
                    continue
                ps, n_here = parse_topic_page(hp)
                new = [x for x in ps if not x["post_id"] or x["post_id"] not in seen_ids]
                if not new:  # 超出最後一頁時 Mobile01 會回傳同一頁內容
                    break
                seen_ids.update(x["post_id"] for x in new if x["post_id"])
                posts.extend(new)
                n = max(n, n_here)
                p += 1
            rec = dict(r)
            rec.update({
                "url": f"{SITE}/topicdetail.php?f={FORUM}&t={t}",
                "page_title": re.sub(r"\s*-\s*Mobile01$", "", title),
                "n_pages": n,
                "n_posts": len(posts),
                "posts": posts,
                "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
            })
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            ok += 1
            if i % 25 == 0:
                log(f"主題進度 {i}/{len(todo)}（成功 {ok}，失敗 {fail}，已 fetch {fetched} 頁）")
            sleep()
    log(f"主題完成：成功 {ok}，失敗 {fail}，fetch {fetched} 頁，檔內共 {len(done) + ok} 主題")


if __name__ == "__main__":
    log("=== 開始 ===")
    idx = build_index()
    crawl_topics(idx)
    log("=== 結束 ===")
    try:
        requests.get(f"{PROXY}/close", params={"target": tab()}, timeout=10)
    except Exception:
        pass
