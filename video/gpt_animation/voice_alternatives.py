"""Audition another available Taiwanese female voice without replacing the film."""
import asyncio,json,subprocess
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'timeline.json').read_text(encoding='utf-8'))
text=data['segments'][1]['text']
OUT=ROOT/'output'/'旁白試聽'

async def main():
    rows=[]
    for name,rate in [('D_HsiaoChen_稍快','+5%'),('E_HsiaoChen_標準','+0%')]:
        raw=OUT/(name+'_raw.mp3');dest=OUT/(name+'.mp3')
        await edge_tts.Communicate(text,'zh-TW-HsiaoChenNeural',rate=rate).save(str(raw))
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af','loudnorm=I=-18:TP=-1.5:LRA=7','-ar','48000','-ac','1','-c:a','libmp3lame','-b:a','192k',str(dest)],check=True)
        subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],check=True)
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(dest)]))
        rows.append(dict(file=dest.name,voice='zh-TW-HsiaoChenNeural',rate=rate,duration=duration))
        print(name,round(duration,2),flush=True)
    (OUT/'另一種女聲.json').write_text(json.dumps(dict(text=text,samples=rows),ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'另一種女聲.md').write_text('\n'.join([
        '# 另一種台灣中文女聲試聽','',
        'D、E 使用 zh-TW-HsiaoChenNeural。原影片與 A、B、C 使用 zh-TW-HsiaoYuNeural。文字皆為原影片第 1 段，未改寫；音量以 -18 LUFS 為目標，無配樂。','',
        '| 試聽 | 聲音 | 語速 |','| --- | --- | --- |',
        '| [B：原聲音，稍慢](B_稍慢.mp3) | HsiaoYu | +5% |',
        '| [D：換聲音，同語速](D_HsiaoChen_稍快.mp3) | HsiaoChen | +5% |',
        '| [C：原聲音，標準速度](C_標準語速.mp3) | HsiaoYu | +0% |',
        '| [E：換聲音，標準速度](E_HsiaoChen_標準.mp3) | HsiaoChen | +0% |','',
        '建議先比較 B、D，兩者使用相同的 +5% 語速參數。更自然與否由實際試聽判斷，未預設新聲音一定較佳。',
        '原影片尚未替換聲音；正式替換後需重新量測全片長度及對齊字幕。',''
    ]),encoding='utf-8')

if __name__=='__main__':asyncio.run(main())
