# -*- coding: utf-8 -*-
"""
tts.py：用 edge-tts（zh-TW-HsiaoYuNeural）逐段合成旁白，量實長並取得逐字時間戳。

用法：
  python tts.py                 # 用 script.json 的 rate 合成全部段落，輸出到 ../out/tts/
  python tts.py --rates         # 試 -5% / -3% / +0% 三種語速，輸出每段實長與字速到 rates_trial.csv
  python tts.py --rate=+10%     # 指定語速
  python tts.py --cuts=2        # 套用 script.json cuts 的前 2 項（v2 第五節的刪減順序）
  python tts.py --only=3,4      # 只重合成指定段

輸出（video/out/tts/）：
  seg{n}.mp3 / seg{n}.wav       旁白（wav 為 48 kHz 單聲道，供 ffmpeg 混音）
  seg{n}.words.json             edge-tts WordBoundary（start / end，單位秒）
  tts_timing.json               每段：字數、語音秒數（duration＝檔長、speech_end＝最後一字結束）、
                                cue（字幕句）與 key（畫面節拍）的時間
  rates_trial.csv               --rates 時各語速的實長比較
"""
import asyncio
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import edge_tts

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out" / "tts"
OUT.mkdir(parents=True, exist_ok=True)
SCRIPT = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
VOICE = SCRIPT["voice"]
RATE = SCRIPT.get("rate", "+0%")  # 預設語速取 script.json；見 README「語速選擇」


def count_chars(s: str) -> int:
    """旁白字數：中文字＋英文／數字單字各算 1，不含標點。"""
    cjk = len(re.findall(r"[一-鿿]", s))
    words = len(re.findall(r"[A-Za-z0-9]+", s))
    return cjk + words


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())


async def synth(text: str, mp3: Path, rate: str):
    """合成一段，回傳 WordBoundary 清單（秒）。"""
    com = edge_tts.Communicate(text, VOICE, rate=rate, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    return words


def to_wav(mp3: Path, wav: Path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "48000", "-ac", "1",
                    "-c:a", "pcm_s16le", str(wav)], check=True)


def map_words_to_text(narration: str, words: list) -> dict:
    """把每個 WordBoundary 對回旁白字串的字元區間：字元索引 → (start, end)。"""
    char_time = {}
    pos = 0
    for w in words:
        tx = w["text"].strip()
        if not tx:
            continue
        i = narration.find(tx, pos)
        if i < 0:
            i = narration.find(tx[0], pos)
            if i < 0:
                continue
        for k in range(i, i + len(tx)):
            char_time[k] = (w["start"], w["end"])
        pos = i + len(tx)
    return char_time


def time_at(narration: str, char_time: dict, phrase: str, which: str = "start") -> float:
    i = narration.find(phrase)
    if i < 0:
        print(f"   （旁白已刪去「{phrase}」，節拍以 0 代入）")
        return 0.0
    if which == "start":
        for k in range(i, len(narration)):
            if k in char_time:
                return char_time[k][0]
    else:
        for k in range(i + len(phrase) - 1, -1, -1):
            if k in char_time:
                return char_time[k][1]
    return 0.0


def apply_cuts(script: dict, n: int) -> list:
    """回傳套用前 n 項刪減後的段落清單（深拷貝），每項 edit 同時套到旁白與字幕句。"""
    import copy
    segs = copy.deepcopy(script["segments"])
    applied = []
    for cut in script.get("cuts", [])[:n]:
        seg = next(s for s in segs if s["id"] == cut["seg"])
        removed = 0
        for old, new in cut["edits"]:
            assert old in seg["narration"], f"cut {cut['id']}：旁白找不到「{old}」"
            seg["narration"] = seg["narration"].replace(old, new, 1)
            hit = [c for c in seg["cues"] if old in c]
            assert hit, f"cut {cut['id']}：「{old}」不在單一字幕句內"
            seg["cues"] = [c.replace(old, new, 1) for c in seg["cues"]]
            removed += count_chars(old) - count_chars(new)
        seg["cues"] = [c for c in seg["cues"] if count_chars(c) > 0]
        applied.append({"id": cut["id"], "name": cut["name"], "seg": cut["seg"], "chars_removed": removed})
    return segs, applied


def build_timing(seg: dict, words: list, dur: float) -> dict:
    nar = seg["narration"]
    ct = map_words_to_text(nar, words)
    cues = []
    pos = 0
    for c in seg["cues"]:
        i = nar.find(c, pos)
        assert i >= 0, f"cue 不在旁白中：{c}"
        cues.append({"text": c, "start": time_at(nar, ct, c, "start"), "end": time_at(nar, ct, c, "end")})
        pos = i + len(c)
    # 每句字幕顯示到下一句開始（避免閃爍）；最後一句到語音結束。最短 2 秒另行標記。
    speech_end = max(w["end"] for w in words) if words else dur
    for j, c in enumerate(cues):
        nxt = cues[j + 1]["start"] if j + 1 < len(cues) else min(dur, speech_end + 0.4)
        c["show_end"] = nxt
        c["too_short"] = (c["show_end"] - c["start"]) < 2.0
    keys = {k: time_at(nar, ct, phrase, "start") for k, phrase in seg["keys"].items()}
    return {"id": seg["id"], "title": seg["title"], "chars": count_chars(nar), "duration": dur,
            "speech_end": speech_end, "cues": cues, "keys": keys}


async def main():
    args = sys.argv[1:]
    rate = RATE
    for a in args:
        if a.startswith("--rate="):
            rate = a.split("=", 1)[1]
    if "--rates" in args:
        rows = []
        for r in ["-5%", "-3%", "+0%"]:
            for seg in SCRIPT["segments"]:
                tag = r.replace("%", "").replace("+", "")
                mp3 = OUT / f"trial_seg{seg['id']}_{tag}.mp3"
                await synth(seg["narration"], mp3, r)
                d = probe_duration(mp3)
                n = count_chars(seg["narration"])
                rows.append({"rate": r, "seg": seg["id"], "chars": n, "sec": round(d, 2),
                             "chars_per_sec": round(n / d, 2)})
                print(rows[-1])
        with open(OUT / "rates_trial.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return
    ncuts = 0
    only = None
    for a in args:
        if a.startswith("--cuts="):
            ncuts = int(a.split("=", 1)[1])
        if a.startswith("--only="):
            only = {int(x) for x in a.split("=", 1)[1].split(",")}
    segments, applied = apply_cuts(SCRIPT, ncuts)
    prev = (OUT / "tts_timing.json")
    prev = json.loads(prev.read_text(encoding="utf-8")) if (only and prev.exists()) else None
    timing = {"voice": VOICE, "rate": rate, "cuts": applied, "segments": []}
    total_speech = 0.0
    for seg in segments:
        if only is not None and seg["id"] not in only and prev:
            old = next((s for s in prev["segments"] if s["id"] == seg["id"]), None)
            if old:
                timing["segments"].append(old); total_speech += old["speech_end"]; continue
        mp3 = OUT / f"seg{seg['id']}.mp3"
        wav = OUT / f"seg{seg['id']}.wav"
        words = await synth(seg["narration"], mp3, rate)
        to_wav(mp3, wav)
        dur = probe_duration(wav)
        (OUT / f"seg{seg['id']}.words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
        t = build_timing(seg, words, dur)
        t["narration"] = seg["narration"]
        timing["segments"].append(t)
        total_speech += t["speech_end"]
        ks = {k: round(v, 2) for k, v in t["keys"].items()}
        print(f"seg{seg['id']}: {t['chars']} 字, {dur:.2f} s, {t['chars'] / dur:.2f} 字/秒; keys={ks}")
        for c in t["cues"]:
            flag = "  <2s!" if c["too_short"] else ""
            print(f"   {c['start']:6.2f}-{c['show_end']:6.2f} {c['text']}{flag}")
    print(f"合計語音（最後一字）{total_speech:.1f} s；套用刪減：{[a['id'] for a in applied]}")
    (OUT / "tts_timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
