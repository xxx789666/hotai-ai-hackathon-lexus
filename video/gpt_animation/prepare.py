import asyncio, json, math, re, subprocess, sys
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
ASSETS = ROOT / 'assets'
for p in [OUT, ASSETS]: p.mkdir(exist_ok=True)
SOURCE = ROOT.parents[1] / '使用場景動畫_製作提示詞_GPT.md'
doc = SOURCE.read_text(encoding='utf-8')
original = [x.strip() for x in doc.split('### 4.')[1].split('### 5.')[0].split('\n\n')[1:] if x.strip()]
assert len(original) == 10
VOICE='zh-TW-HsiaoYuNeural'
RATE='+10%'

def duration(p):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)]))

async def synth(i, text, sem):
    tag = 'full' if text == original[i] else 'cut'
    mp3=ASSETS/f'voice_{i}_{tag}.mp3'; meta=mp3.with_suffix('.json')
    if meta.exists() and mp3.exists():
        data=json.loads(meta.read_text(encoding='utf-8'))
        if data['text']==text: return data
    async with sem:
        words=[]
        com=edge_tts.Communicate(text, VOICE, rate=RATE, boundary='WordBoundary')
        with mp3.open('wb') as f:
            async for c in com.stream():
                if c['type']=='audio': f.write(c['data'])
                elif c['type']=='WordBoundary': words.append(dict(text=c['text'], start=c['offset']/1e7, end=(c['offset']+c['duration'])/1e7))
        data=dict(id=i,text=text,words=words,audio=str(mp3),speech_end=words[-1]['end'],duration=duration(mp3))
        meta.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'voice {i}: {data["speech_end"]:.2f}s',flush=True)
        return data

def captions(s):
    text=s['text']; n=len(text); words=s['words']; starts={0:0.0}; pos=0
    for w in words:
        idx=text.find(w['text'],pos)
        if idx < 0: raise ValueError((w,text[pos:]))
        if idx: starts[idx]=w['start']
        pos=idx+len(w['text'])
    # Boundary includes punctuation/spaces with preceding spoken clause.
    starts[n]=s['speech_end']+0.8
    # Never split a contiguous English name or identifier such as Mobile01.
    pts=sorted(i for i in starts if i in (0,n) or not (text[i-1].isascii() and text[i].isascii() and text[i-1].isalnum() and text[i].isalnum()))
    dp={n:(0,[])}
    for i in reversed(pts[:-1]):
        opts=[]
        for j in pts:
            if j<=i or j-i>22 or j not in dp: continue
            dt=starts[j]-starts[i]
            if dt < 2.001: continue
            boundary=0 if text[j-1] in '，。；：？！、' else 45
            if j==n: boundary=0
            internal=sum(text[i:j-1].count(mark)*weight for mark,weight in [('。',28),('；',16),('？',28)])
            cost=(j-i-15)**2*.03+boundary+internal+dp[j][0]
            opts.append((cost,[dict(text=text[i:j],start=starts[i],end=starts[j])]+dp[j][1]))
        if opts: dp[i]=min(opts,key=lambda x:x[0])
    if 0 not in dp: raise ValueError(f'No feasible captions scene {s["id"]}')
    return dp[0][1]

async def main():
    sem=asyncio.Semaphore(3)
    segs=await asyncio.gather(*(synth(i,t,sem) for i,t in enumerate(original)))
    cuts=[]
    def total(): return sum(math.ceil((s['speech_end']+1.4)*30)/30 for s in segs)+2.4
    print('Full duration',total(),flush=True)
    edits=[(3,[('，人數最多',''),('修不好就',''),('自己走，還',''),('從不抱怨，','')]),(6,[('每則草稿旁邊，都附著引用的條款編號。','')]),(1,[('這一次，他有了新的幫手。','')]),(8,[('，校正下一次的判斷','')])]
    for num,(i,replacements) in enumerate(edits,1):
        if total()<=178: break
        text=original[i]
        for a,b in replacements: text=text.replace(a,b)
        segs[i]=await synth(i,text,sem)
        cuts.append(dict(item=num,scene=i,edits=replacements))
        print('Cut',num,'duration',total(),flush=True)
    assert total()<=178, total()
    offset=0
    for s in segs:
        s['lead']=1.2 if s['id']==0 else .3
        s['duration']=math.ceil((s['speech_end']+1.4)*30)/30 + (0.9 if s['id']==0 else 1.5 if s['id']==9 else 0)
        s['start']=offset; offset+=s['duration']; s['end']=offset
        s['cues']=captions(s)
    result=dict(voice=VOICE,rate=RATE,cuts=cuts,duration=offset,segments=segs)
    (ROOT/'timeline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    def stamp(v):
        ms=round(v*1000); return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    entries=[]
    for s in segs:
        for c in s['cues']:
            entries.append(f'{len(entries)+1}\n{stamp(s["start"]+s["lead"]+c["start"])} --> {stamp(s["start"]+s["lead"]+c["end"])}\n{c["text"]}\n')
    (OUT/'scene_animation.srt').write_text('\n'.join(entries),encoding='utf-8-sig')
    print('READY',offset,'seconds;',len(entries),'captions',flush=True)

if __name__=='__main__': asyncio.run(main())
