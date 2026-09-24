# -*- coding: utf-8 -*-
"""
爬取 Dcard 與 Lexus 相關的貼文（全文 + 留言）。
Dcard 有 Cloudflare 人機驗證，curl/Jina 皆不可用；本程式透過 web-access CDP proxy（127.0.0.1:3456）
在使用者 Chrome 分頁內 fetch 站內 API：
  /service/api/v2/search/posts?query=..&limit=30&offset=N
  /service/api/v2/posts/<id>
  /service/api/v2/posts/<id>/comments?limit=30[&after=<floor>]
可續跑：已抓過的貼文（以 id 為 key）會跳過。
輸出：
  data/dcard/lexus_search_index.jsonl  搜尋結果索引（去重，含命中的查詢詞）
  data/dcard/lexus_posts.jsonl         每篇一行：meta + content + comments[]
  data/dcard/crawl.log
"""
import json, os, re, sys, time, random, pathlib, datetime
from urllib.parse import quote
import requests

PROXY = "http://127.0.0.1:3456"
SITE = "https://www.dcard.tw"
QUERIES = ["lexus", "凌志", "lexus 保養", "lexus 原廠", "lexus 保固", "lexus 維修", "lexus 車主"]
MAX_OFFSET = 6000
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "dcard"
OUT.mkdir(parents=True, exist_ok=True)
INDEX = OUT / "lexus_search_index.jsonl"
POSTS = OUT / "lexus_posts.jsonl"
LOG = OUT / "crawl.log"
TAB_FILE = OUT / "tab_id.txt"
DELAY = tuple(float(x) for x in os.environ.get("DC_DELAY", "1.8,2.4").split(","))


def log(msg):
    line = f"{datetime.datetime.now():%H:%M:%S} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sleep():
    time.sleep(random.uniform(*DELAY))


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
    r = requests.get(f"{PROXY}/new", params={"url": f"{SITE}/f/car"}, timeout=60).json()
    _tab = r["targetId"]
    TAB_FILE.write_text(_tab)
    time.sleep(6)
    log(f"新開分頁 {_tab}")
    return _tab


def api(path, tries=5):
    """在頁面內 fetch 站內 API，回傳解析後的 JSON；429 退避。path 必須是 ASCII（中文先 percent-encode）。"""
    global _tab
    js = ('(async()=>{try{const r=await fetch(%s,{credentials:"include"});'
          'const t=await r.text();return JSON.stringify({s:r.status,t});}'
          'catch(e){return JSON.stringify({s:-1,t:String(e)});}})()') % json.dumps(path)
    for i in range(tries):
        try:
            resp = requests.post(f"{PROXY}/eval", params={"target": tab()}, data=js.encode("ascii"), timeout=60)
            j = resp.json()
            if "error" in j:
                log(f"eval error {j['error']} (try {i+1})")
                _tab = None
                time.sleep(5)
                continue
            v = json.loads(j["value"]) if isinstance(j["value"], str) else j["value"]
            s = v.get("s")
            if s == 200:
                try:
                    return json.loads(v["t"])
                except Exception:
                    log(f"非 JSON 回應 {path}（可能是人機驗證頁），退避 90s")
                    time.sleep(90)
                    continue
            if s == 404:
                return None
            if s == 429:
                log(f"429 {path} (try {i+1})，退避 {90 + 60 * i}s")
                time.sleep(90 + 60 * i)
                continue
            log(f"HTTP {s} {path} (try {i+1})")
            time.sleep(10)
        except Exception as e:
            log(f"ERR {e} {path} (try {i+1})")
            time.sleep(5)
    return None


# ---------- 1. 搜尋索引 ----------
def build_index():
    if INDEX.exists():
        rows = [json.loads(l) for l in INDEX.open(encoding="utf-8")]
        log(f"索引已存在，{len(rows)} 筆，略過搜尋階段")
        return rows
    seen = {}
    for q in QUERIES:
        qe = quote(q)
        off, got = 0, 0
        while off < MAX_OFFSET:
            j = api(f"/service/api/v2/search/posts?query={qe}&limit=30&offset={off}")
            if not j or not isinstance(j, list):
                break
            for p in j:
                pid = p.get("id")
                if not pid:
                    continue
                if pid in seen:
                    seen[pid]["queries"].append(q)
                else:
                    seen[pid] = {
                        "id": pid, "title": p.get("title"), "forum": p.get("forumAlias"),
                        "forumName": p.get("forumName"), "createdAt": p.get("createdAt"),
                        "commentCount": p.get("commentCount"), "likeCount": p.get("likeCount"),
                        "excerpt": p.get("excerpt"), "queries": [q],
                    }
            got += len(j)
            off += len(j)
            if len(j) < 30:
                break
            if off % 300 == 0:
                log(f"查詢「{q}」offset {off}，累計去重 {len(seen)} 篇")
            sleep()
        log(f"查詢「{q}」完成：{got} 筆，累計去重 {len(seen)} 篇")
        sleep()
    rows = sorted(seen.values(), key=lambda r: r["createdAt"] or "", reverse=True)
    with INDEX.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"索引完成：{len(rows)} 篇")
    return rows


# ---------- 2. 貼文內容 + 留言 ----------
def fetch_comments(pid, expected):
    out, after = [], None
    while True:
        path = f"/service/api/v2/posts/{pid}/comments?limit=30" + (f"&after={after}" if after is not None else "")
        j = api(path)
        if not j or not isinstance(j, list):
            break
        for c in j:
            out.append({
                "id": c.get("id"), "floor": c.get("floor"), "createdAt": c.get("createdAt"),
                "content": c.get("content"), "likeCount": c.get("likeCount"),
                "hidden": bool(c.get("hidden")), "school": c.get("school"), "gender": c.get("gender"),
            })
        if len(j) < 30:
            break
        last = j[-1].get("floor")
        if last is None or last == after:
            break
        after = last
        sleep()
    return out


def crawl_posts(index):
    done = set()
    if POSTS.exists():
        for l in POSTS.open(encoding="utf-8"):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
    todo = [r for r in index if r["id"] not in done]
    log(f"貼文階段：已抓 {len(done)}，待抓 {len(todo)}")
    ok = fail = 0
    with POSTS.open("a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            pid = r["id"]
            d = api(f"/service/api/v2/posts/{pid}")
            if not d or not isinstance(d, dict):
                fail += 1
                log(f"失敗/不存在：{pid}")
                sleep()
                continue
            comments = []
            if (d.get("commentCount") or 0) > 0:
                sleep()
                comments = fetch_comments(pid, d.get("commentCount"))
            rec = {
                "id": pid, "url": f"{SITE}/f/{d.get('forumAlias')}/p/{pid}",
                "title": d.get("title"), "forum": d.get("forumAlias"), "forumName": d.get("forumName"),
                "createdAt": d.get("createdAt"), "updatedAt": d.get("updatedAt"),
                "school": d.get("school"), "gender": d.get("gender"),
                "commentCount": d.get("commentCount"), "likeCount": d.get("likeCount"),
                "topics": d.get("topics"), "content": d.get("content"),
                "comments": comments, "n_comments_fetched": len(comments),
                "queries": r.get("queries"),
                "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            ok += 1
            if i % 50 == 0:
                log(f"貼文進度 {i}/{len(todo)}（成功 {ok}，失敗 {fail}）")
            sleep()
    log(f"貼文完成：成功 {ok}，失敗 {fail}，檔內共 {len(done) + ok} 篇")


if __name__ == "__main__":
    log("=== 開始 ===")
    idx = build_index()
    crawl_posts(idx)
    log("=== 結束 ===")
    try:
        requests.get(f"{PROXY}/close", params={"target": tab()}, timeout=10)
        TAB_FILE.unlink(missing_ok=True)
    except Exception:
        pass
