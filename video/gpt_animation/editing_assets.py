"""Create a subtitle editing document once, plus explicitly keyed voice auditions."""
import asyncio, json, subprocess
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'timeline.json').read_text(encoding='utf-8'))
OUT=ROOT/'output'/'旁白試聽'
OUT.mkdir(exist_ok=True)
DOC=ROOT.parents[1]/'使用場景動畫_字幕與旁白_編修稿.md'

def stamp(t):
    ms=round(t*1000)
    return f'{ms//60000:02}:{ms//1000%60:02}.{ms%1000:03}'

def document():
    if DOC.exists():
        print('Editing document exists; preserving edits.',flush=True)
        return
    lines=['# 使用場景動畫｜字幕與旁白編修稿','',
    '建立日期：2026-10-05。底稿：GPT 製作版 `video/gpt_animation/output/scene_animation.mp4`，全長 2:56.933，共 10 段、51 則字幕。','',
    '## 怎麼修改','',
    '- 直接修改各表格的「字幕／旁白文字」欄。這一欄是本編修稿的文字主稿，避免字幕、旁白各改一份。',
    '- 新增句子：在對應段落新增一列，編號填「新增」、時間填「待重排」。刪除句子：刪除該列。',
    '- 修改或新增文字後，時間碼只是舊版參考；重製時需重新配音、分句與對齊畫面。無須自行計算時間。',
    '- 字幕的列與換行用於畫面顯示；配音需按完整語意組合，不要將每一列硬切成一段音訊。',
    '- 「配音備註」可填希望強調的詞、需要停頓的位置或英文讀法；備註不會被唸出。',
    '- 目前程式仍讀取原製作提示詞。本 MD 是獨立編修稿，修改後不會自動改動既有 MP4、SRT 或原提示詞；下次重製時須明確以此稿為準。',
    '- 原製作規格為總長不超過 2:58、每行不超過 22 字、每則字幕至少 2 秒。新增內容後要重新檢查，不能直接沿用目前時間碼。','',
    '## 本版已套用的刪減','',
    '只套用原提示詞第 6 節第一項：第 3 段刪除「，人數最多」「修不好就」「自己走，還」「從不抱怨，」。以下已是刪減後的實際影片字幕，其餘旁白保留。','']
    names=['開場：人走了才知道','產出 1：資料來源與去識別','產出 1：AI 逐句判讀與高風險議題','產出 1：四種客群','產出 1：風險分級與經理的看板','產出 2：接觸點與時機','產出 2：AI 生成內容與條款查核','產出 2：人工審核','產出 2：投遞與回饋','收尾']
    n=0;source_text=[];md_text=[]
    for s in data['segments']:
        lines += [f'## 第 {s["id"]} 段｜{names[s["id"]]}','',
        f'目前畫面時間：{stamp(s["start"])}–{stamp(s["end"])}。','',
        '配音備註：待填。','',
        '| 編號 | 目前開始 | 目前結束 | 字幕／旁白文字 |',
        '| --- | --- | --- | --- |']
        for c in s['cues']:
            n+=1;t=c['text'].strip()
            lines.append(f'| {n:03} | {stamp(s["start"]+s["lead"]+c["start"])} | {stamp(s["start"]+s["lead"]+c["end"])} | {t} |')
            md_text.append(t);source_text.append(c['text'])
        lines.append('')
    lines+=['## 修改紀錄','',
    '| 日期 | 修改內容 |','| --- | --- |',
    '| 2026-10-05 | 從現有影片的 51 則字幕建立編修稿；未改寫內容，僅去除表格欄位頭尾空白。 |','']
    assert ''.join(''.join(md_text).split())==''.join(''.join(source_text).split())
    assert n==51
    DOC.write_text('\n'.join(lines),encoding='utf-8')
    print('MD created: 51 captions, text matched.',flush=True)

def encode(src,dst):
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-af','loudnorm=I=-18:TP=-1.5:LRA=7','-ar','48000','-ac','1','-c:a','libmp3lame','-b:a','192k',str(dst)],check=True)

async def samples():
    s=data['segments'][1];items=[]
    for label,rate in [('A_目前語速','+10%'),('B_稍慢','+5%'),('C_標準語速','+0%')]:
        raw=OUT/f'{label}_raw.mp3';dst=OUT/f'{label}.mp3'
        if rate=='+10%':raw=Path(s['audio'])
        else:
            await edge_tts.Communicate(s['text'],data['voice'],rate=rate).save(str(raw))
        encode(raw,dst)
        seconds=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(dst)]))
        items.append((label,rate,seconds))
        print(label,rate,seconds,flush=True)
    notes=['# 同文同聲三種語速試聽','',
    '取自第 1 段，包含 Lexus、PTT、Mobile01、Dcard，便於比較中英文切換。三版使用相同旁白文字與 zh-TW-HsiaoYuNeural；沒有背景配樂，音量统一為 -18 LUFS 目標。A 取自目前配音；B、C 重新合成，只有語速參數不同。',
    '','| 試聽 | 語速參數 | 音檔秒數 |','| --- | --- | --- |']
    notes += [f'| [{lab}]({lab}.mp3) | {rate} | {seconds:.2f} |' for lab,rate,seconds in items]
    notes += ['','原文：','',s['text'],'',
    '目前全片只有約 1.07 秒餘裕。這些是試聽音檔，尚未替換影片；全片放慢後必須重新量測時長，並依原規格安排刪減與字幕。',
    '','可留意：語尾是否太趕、英文名稱是否清楚、逗號停頓是否自然，以及敘事是否連贯。速度試聽不等於已修正發音或停頓。','']
    (OUT/'試聽說明.md').write_text('\n'.join(notes),encoding='utf-8')

if __name__=='__main__':
    document()
    asyncio.run(samples())
