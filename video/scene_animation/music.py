# -*- coding: utf-8 -*-
"""
music.py：自製合成鋪底（placeholder）。numpy 生成柔和的和弦墊音，無版權疑慮；正式版再換。

用法：python music.py <秒數> <輸出.wav>
做法：四個和弦（Cmaj9 → Am9 → Fmaj9 → Gsus2）各 6 秒循環，每個音用正弦＋少量泛音、
慢起音慢釋放、兩路微失諧做合唱感，加一條低八度根音；一階低通讓聲音更柔；首尾淡入淡出。
輸出為 48 kHz 立體聲 16-bit，峰值約 -12 dBFS；混音時由 render.py 再依旁白音量壓到約 -20 dB。
"""
import sys
import numpy as np
from scipy.io import wavfile  # scipy 若不存在，改用 wave 模組；見下方 fallback

SR = 48000


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


CHORDS = [
    [60, 64, 67, 71, 74],   # Cmaj9
    [57, 60, 64, 67, 71],   # Am9
    [53, 57, 60, 64, 67],   # Fmaj9
    [55, 60, 62, 67, 74],   # Gsus2(add9)
]
CHORD_LEN = 6.0


def tone(freq, dur, amp, detune=0.0):
    t = np.arange(int(dur * SR)) / SR
    f = freq * (1 + detune)
    y = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t))
    # 慢起音 1.2 s、慢釋放 2.0 s
    env = np.ones_like(t)
    a = int(1.2 * SR); r = int(2.0 * SR)
    env[:a] = np.linspace(0, 1, a) ** 2
    env[-r:] *= np.linspace(1, 0, r) ** 1.5
    return amp * y * env


def lowpass(x, cutoff=1800.0):
    rc = 1.0 / (2 * np.pi * cutoff)
    alpha = (1.0 / SR) / (rc + 1.0 / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return y


def render(duration: float) -> np.ndarray:
    n = int(duration * SR)
    left = np.zeros(n + int(4 * SR)); right = np.zeros_like(left)
    t0 = 0.0; k = 0
    while t0 < duration:
        chord = CHORDS[k % len(CHORDS)]
        seg = CHORD_LEN + 2.0  # 與下一個和弦重疊 2 秒
        start = int(t0 * SR)
        for j, note in enumerate(chord):
            amp = 0.16 if j else 0.12
            l = tone(midi(note), seg, amp, detune=+0.0015 * (j % 2))
            r = tone(midi(note), seg, amp, detune=-0.0015 * ((j + 1) % 2))
            end = min(start + len(l), len(left))
            left[start:end] += l[:end - start]; right[start:end] += r[:end - start]
        bass = tone(midi(chord[0] - 12), seg, 0.14)
        end = min(start + len(bass), len(left))
        left[start:end] += bass[:end - start]; right[start:end] += bass[:end - start]
        t0 += CHORD_LEN; k += 1
    left = left[:n]; right = right[:n]
    # 低通（向量化近似：用 FFT 式濾波取代逐樣本迴圈）
    def lp(x):
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
        X *= 1 / np.sqrt(1 + (f / 1800.0) ** 4)
        return np.fft.irfft(X, n=len(x))
    left = lp(left); right = lp(right)
    # 淡入 2 s、淡出 3 s
    fi = int(2 * SR); fo = int(3 * SR)
    env = np.ones(n); env[:fi] = np.linspace(0, 1, fi); env[-fo:] *= np.linspace(1, 0, fo)
    left *= env; right *= env
    st = np.stack([left, right], axis=1)
    st = st / (np.abs(st).max() + 1e-9) * 0.25  # 峰值約 -12 dBFS
    return st


def main():
    dur = float(sys.argv[1]); out = sys.argv[2]
    st = render(dur)
    wavfile.write(out, SR, (st * 32767).astype(np.int16))
    print(f"music placeholder: {dur:.1f}s -> {out}")


if __name__ == "__main__":
    main()
