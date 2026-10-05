# -*- coding: utf-8 -*-
"""
render.py：用 Playwright 逐格決定論渲染三個場景 → ffmpeg 合成 1920×1080、30 fps、H.264＋AAC。

流程：
  1. 讀 script.json、../out/tts/tts_timing.json（先跑 tts.py）。
  2. 每段場景長度 = lead（進場／開場）＋ 語音實長（最後一字結束）＋ 0.8 秒停留 ＋ 出場轉場。
  3. 開 scenes/seg{n}.html?T=..&lead=..&k_xxx=..，注入字幕 cue，逐格 seek(t) 截 1920×1080 幀到 ../out/frames/seg{n}/。
  4. 每段編成 seg{n}.mp4，concat；旁白依時間軸 adelay，鋪底（music.py）壓到旁白 RMS 之下 20 dB，amix。
  5. 另輸出 scene_animation_full.srt、timing.csv、full_contact.png（每 4 秒抽一格）。

用法：
  python render.py            # 全部重跑
  python render.py --snap     # 只每 3 秒抽格出縮圖總表（快速看版面）
  python render.py --no-frames  # 跳過截圖，只重做編碼／混音（frames 已存在時）
  python render.py --png      # 幀存 PNG（無損但慢約 8 倍）；預設 JPEG q95
  python render.py --segs=0,1,2 --name=sample_seg0-2   # 只做部分段落（樣片）
  （截圖三段平行跑，各自一個 Chromium；約 2,000 格需數分鐘）
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
FRAMES = OUT / "frames"
TTS = OUT / "tts"
FPS = 30
W, H = 1920, 1080
FRAME_EXT = "jpg"   # 預設 JPEG q95（PNG 編碼約慢 8 倍）；--png 改存 PNG
FRAME_KW = {"type": "jpeg", "quality": 95}
HOLD_AFTER_SPEECH = 0.8   # 旁白結束後畫面至少停 0.8 秒
NAME = "scene_animation_full"
CONTACT_EVERY = 4.0       # 縮圖總表每幾秒抽一格

# 每段的轉場與開場設定（秒）。段間停頓＝出場半段＋進場半段：光掃 0.3+0.3、大光暈 0.4+0.4（1→2、4→5：產出 1 → 產出 2）。
# seg0 開場是深色粒子（intro 2.4）；seg9 的 dout 是片尾字卡 4 秒（字卡畫在場景裡），最後 0.8 秒由 ffmpeg 淡白。
SW, GL = 0.3, 0.4
SEG_CFG = {
    0: {"in": "none", "din": 0.0, "out": "sweep", "dout": SW, "intro": 2.4},
    1: {"in": "sweep", "din": SW, "out": "glow", "dout": GL, "intro": 0.0},
    2: {"in": "glow", "din": GL, "out": "sweep", "dout": SW, "intro": 0.0},
    3: {"in": "sweep", "din": SW, "out": "sweep", "dout": SW, "intro": 0.0},
    4: {"in": "sweep", "din": SW, "out": "glow", "dout": GL, "intro": 0.0},
    5: {"in": "glow", "din": GL, "out": "sweep", "dout": SW, "intro": 0.0},
    6: {"in": "sweep", "din": SW, "out": "sweep", "dout": SW, "intro": 0.0},
    7: {"in": "sweep", "din": SW, "out": "sweep", "dout": SW, "intro": 0.0},
    8: {"in": "sweep", "din": SW, "out": "sweep", "dout": SW, "intro": 0.0},
    9: {"in": "sweep", "din": SW, "out": "none", "dout": 4.0, "intro": 0.0},
}
END_FADE = 0.8


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd)[:300])
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def plan(only=None):
    """算每段 lead / T / 全域起點，回傳清單。"""
    timing = json.loads((TTS / "tts_timing.json").read_text(encoding="utf-8"))
    segs = []
    cursor = 0.0
    for s in timing["segments"]:
        if only is not None and s["id"] not in only:
            continue
        c = SEG_CFG[s["id"]]
        lead = c["din"] + c["intro"]
        T = lead + s["speech_end"] + HOLD_AFTER_SPEECH + c["dout"]
        T = round(T * FPS) / FPS
        segs.append({
            "id": s["id"], "title": s["title"], "chars": s["chars"],
            "audio_len": s["duration"], "speech_end": s["speech_end"],
            "lead": lead, "T": T, "start": cursor, "cfg": c,
            "keys": s["keys"], "cues": s["cues"],
        })
        cursor += T
    return timing, segs, cursor


def scene_url(seg):
    c = seg["cfg"]
    q = {"T": seg["T"], "lead": seg["lead"], "in": c["in"], "out": c["out"], "din": c["din"], "dout": c["dout"]}
    q.update(seg["keys"])
    return (HERE / "scenes" / f"seg{seg['id']}.html").resolve().as_uri() + "?" + "&".join(f"{k}={v}" for k, v in q.items())


def open_scene(browser, seg):
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    page.add_init_script("window.__RENDER__=true; window.CUES=" + json.dumps(seg["cues"], ensure_ascii=False))
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(scene_url(seg))
    page.wait_for_function("document.fonts.status === 'loaded'")
    page.wait_for_timeout(300)
    if errors:
        raise RuntimeError(f"seg{seg['id']} 頁面錯誤：{errors}")
    return page


def render_one(seg):
    """單一段落逐格截圖（獨立程序，三段平行跑）。"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = open_scene(browser, seg)
        d = FRAMES / f"seg{seg['id']}"
        d.mkdir(parents=True, exist_ok=True)
        n = int(round(seg["T"] * FPS))
        for i in range(n):
            page.evaluate(f"seek({i / FPS})")
            page.screenshot(path=str(d / f"f{i:05d}.{FRAME_EXT}"), **FRAME_KW)
            if i % 150 == 0:
                print(f"   seg{seg['id']} {i}/{n}", flush=True)
        page.close()
        browser.close()
    return seg["id"], n


def render_frames(segs, snap=False):
    snaps = []
    if snap:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for seg in segs:
                page = open_scene(browser, seg)
                for t in [x * 3.0 for x in range(int(seg["T"] // 3) + 1)]:
                    page.evaluate(f"seek({t})")
                    f = OUT / "snap" / f"seg{seg['id']}_{t:05.1f}.png"
                    f.parent.mkdir(exist_ok=True)
                    page.screenshot(path=str(f))
                    snaps.append(f)
                page.close()
            browser.close()
        return snaps
    from concurrent.futures import ProcessPoolExecutor
    for seg in segs:
        print(f"seg{seg['id']}: T={seg['T']:.2f}s, {int(round(seg['T'] * FPS))} 格, lead={seg['lead']:.2f}", flush=True)
    with ProcessPoolExecutor(max_workers=min(5, len(segs))) as ex:
        for sid, n in ex.map(render_one, segs):
            print(f"seg{sid} done: {n} 格", flush=True)
    return snaps


def encode(segs, total):
    OUT.mkdir(exist_ok=True)
    parts = []
    for seg in segs:
        mp4 = OUT / f"seg{seg['id']}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-framerate", FPS, "-i", FRAMES / f"seg{seg['id']}" / f"f%05d.{FRAME_EXT}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS, mp4])
        parts.append(mp4)
    lst = OUT / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    silent = OUT / f"{NAME}_video.mp4"
    # 串接後尾端淡白 0.8 秒（重新編碼一次，順便統一參數）
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-vf", f"fade=t=out:st={total - END_FADE:.3f}:d={END_FADE}:color=white",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS, silent])
    return silent


def rms_db(wav: Path) -> float:
    import numpy as np
    from scipy.io import wavfile
    sr, x = wavfile.read(wav)
    x = x.astype("float64") / 32768.0
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = x[np.abs(x) > 0.01] if (np.abs(x) > 0.01).any() else x  # 只量有聲部分
    return 20 * float(np.log10(np.sqrt((x ** 2).mean()) + 1e-9))


def mix_audio(segs, total):
    music = OUT / "music_placeholder.wav"
    run([sys.executable, HERE / "music.py", f"{total:.2f}", music])
    narr_db = sum(rms_db(TTS / f"seg{s['id']}.wav") for s in segs) / len(segs)
    music_db = rms_db(music)
    gain = (narr_db - 20.0) - music_db   # 鋪底 RMS 壓到旁白之下 20 dB
    print(f"narration RMS {narr_db:.1f} dBFS, music RMS {music_db:.1f} dBFS → music gain {gain:+.1f} dB")
    inputs = []
    fc = []
    for i, s in enumerate(segs):
        inputs += ["-i", TTS / f"seg{s['id']}.wav"]
        delay = int(round((s["start"] + s["lead"]) * 1000))
        fc.append(f"[{i}]adelay={delay}|{delay},apad[n{i}]")
    inputs += ["-i", music]
    m = len(segs)
    fc.append(f"[{m}]volume={gain:.2f}dB[mu]")
    fc.append("".join(f"[n{i}]" for i in range(m)) + f"[mu]amix=inputs={m + 1}:normalize=0:duration=first,atrim=0:{total:.3f}[a]")
    mixed = OUT / f"{NAME}_audio.wav"
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc), "-map", "[a]", "-ar", "48000", "-ac", "2", mixed])
    return mixed


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(segs):
    lines = []
    k = 1
    for s in segs:
        base = s["start"] + s["lead"]
        for c in s["cues"]:
            lines.append(f"{k}\n{srt_time(base + c['start'])} --> {srt_time(base + c['show_end'])}\n{c['text']}\n")
            k += 1
    (OUT / f"{NAME}.srt").write_text("\n".join(lines), encoding="utf-8")


def write_csv(segs, timing):
    csvname = "timing.csv" if NAME == "scene_animation_full" else f"{NAME}_timing.csv"
    with open(OUT / csvname, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["段", "段落", "旁白字數", "語音秒數(檔長)", "語音秒數(最後一字)", "旁白起點(段內)", "場景秒數", "累計秒數", "語速", "聲音"])
        cum = 0.0
        for s in segs:
            cum += s["T"]
            w.writerow([s["id"], s["title"], s["chars"], f"{s['audio_len']:.2f}", f"{s['speech_end']:.2f}",
                        f"{s['lead']:.2f}", f"{s['T']:.2f}", f"{cum:.2f}", timing["rate"], timing["voice"]])
        for c in timing.get("cuts", []):
            w.writerow([f"刪減 {c['id']}", c["name"], f"-{c['chars_removed']}", "", "", "", "", "", "", ""])


def contact_sheet(segs, total, video: Path):
    """每 3 秒從成片抽一格做縮圖總表（驗收用）。"""
    d = OUT / "contact"; d.mkdir(exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-vf", f"fps=1/{CONTACT_EVERY},scale=480:270", d / "c%03d.png"])
    fs = sorted(d.glob("c*.png"))
    cols = 5
    rows = (len(fs) + cols - 1) // cols
    sheet = Image.new("RGB", (480 * cols, 270 * rows), "white")
    for i, f in enumerate(fs):
        sheet.paste(Image.open(f), ((i % cols) * 480, (i // cols) * 270))
    sheet.save(OUT / f"{NAME.replace('scene_animation_', '')}_contact.png")


def main():
    global FRAME_EXT, FRAME_KW, NAME
    args = sys.argv[1:]
    if "--png" in args:
        FRAME_EXT, FRAME_KW = "png", {}
    only = None
    for a in args:
        if a.startswith("--segs="):
            only = {int(x) for x in a.split("=", 1)[1].split(",")}
        if a.startswith("--name="):
            NAME = a.split("=", 1)[1]
    timing, segs, total = plan(only)
    for s in segs:
        print(f"seg{s['id']}: start={s['start']:.2f} lead={s['lead']:.2f} speech={s['speech_end']:.2f} T={s['T']:.2f}")
    print(f"total ≈ {total:.2f}s")
    if "--snap" in args:
        snaps = render_frames(segs, snap=True)
        cols = 5
        rows = (len(snaps) + cols - 1) // cols
        sheet = Image.new("RGB", (480 * cols, 270 * rows), "white")
        for i, f in enumerate(snaps):
            sheet.paste(Image.open(f).resize((480, 270)), ((i % cols) * 480, (i // cols) * 270))
        sheet.save(OUT / "snap" / "snap_sheet.png")
        print("snap sheet:", OUT / "snap" / "snap_sheet.png")
        return
    if "--no-frames" not in args:
        render_frames(segs)
    video = encode(segs, total)
    audio = mix_audio(segs, total)
    final = OUT / f"{NAME}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", final])
    write_srt(segs)
    write_csv(segs, timing)
    contact_sheet(segs, total, final)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(final)],
                       capture_output=True, text=True)
    print(f"done: {final}  duration={float(r.stdout):.2f}s")


if __name__ == "__main__":
    main()
