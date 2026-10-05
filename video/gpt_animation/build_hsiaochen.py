"""Rebuild the existing film using the user's selected D voice and +5% rate."""
import asyncio,copy,hashlib,json,math,os,re,subprocess,sys
from pathlib import Path
import edge_tts
from prepare import captions

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'/'hsiaochen_v2'
ASSETS=ROOT/'assets'/'hsiaochen_v2'
VOICE='zh-TW-HsiaoChenNeural';RATE='+5%'
DOC=ROOT.parents[1]/'使用場景動畫_字幕與旁白_編修稿.md'
for p in [OUT,ASSETS]:p.mkdir(parents=True,exist_ok=True)
old=json.loads((ROOT/'timeline.json').read_text(encoding='utf-8'))

def validate_editing_doc():
    raw=DOC.read_text(encoding='utf-8')
    sections=re.split(r'^## 第 (\d+) 段[^\n]*\n',raw,flags=re.M)
    assert len(sections)==21,'Expected 10 editing sections'
    for k in range(1,len(sections),2):
        i=int(sections[k]);rows=re.findall(r'^\| \d{3} \|[^|]*\|[^|]*\| (.*?) \|$',sections[k+1],re.M)
        txt=''.join(rows)
        assert ''.join(txt.split())==''.join(old['segments'][i]['text'].split()),f'MD scene {i} was edited: review before voice-only replacement.'
    return raw

async def synth(s,sem):
    key=hashlib.sha256((VOICE+RATE+s['text']).encode('utf-8')).hexdigest()[:12]
    path=ASSETS/f'voice_{s["id"]}_{key}.mp3';meta=path.with_suffix('.json')
    if path.exists() and meta.exists():return json.loads(meta.read_text(encoding='utf-8'))
    async with sem:
        words=[]
        with path.open('wb') as f:
            async for c in edge_tts.Communicate(s['text'],VOICE,rate=RATE,boundary='WordBoundary').stream():
                if c['type']=='audio':f.write(c['data'])
                elif c['type']=='WordBoundary':words.append(dict(text=c['text'],start=c['offset']/1e7,end=(c['offset']+c['duration'])/1e7))
        assert words
        result=dict(id=s['id'],text=s['text'],audio=str(path),words=words,speech_end=words[-1]['end'])
        meta.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Voice',s['id'],round(result['speech_end'],2),'s',flush=True)
        return result

def stamp(t,full=False):
    ms=round(t*1000)
    if full:return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    return f'{ms//60000:02}:{ms//1000%60:02}.{ms%1000:03}'

def update_doc(raw,data):
    if DOC.read_text(encoding='utf-8')!=raw:
        print('MD changed during render: preserving user edits; refreshed timeline in output only.',flush=True)
        return
    backup=ASSETS/'字幕編修稿_換聲前備份.md'
    if not backup.exists():backup.write_text(raw,encoding='utf-8')
    count=sum(len(s['cues']) for s in data['segments'])
    updated=re.sub(r'底稿：.*?共 10 段、\d+ 則字幕。',f'底稿：HsiaoChen +5% 版 `video/gpt_animation/output/hsiaochen_v2/scene_animation.mp4`，全長 {stamp(data["duration"])}，共 10 段、{count} 則字幕。',raw,count=1)
    updated=updated.replace('目前程式仍讀取原製作提示詞。本 MD 是獨立編修稿，修改後不會自動改動既有 MP4、SRT 或原提示詞；下次重製時須明確以此稿為準。','本 MD 已與 HsiaoChen +5% 版核對並更新時間碼。修改後不會自動改動影片或配音；下次重製時以本稿為準，重新產生字幕時間。')
    parts=re.split(r'(^## 第 \d+ 段[^\n]*\n)',updated,flags=re.M)
    n=0
    for j in range(1,len(parts),2):
        i=int(re.search(r'第 (\d+) 段',parts[j])[1]);s=data['segments'][i]
        block=parts[j+1]
        block=re.sub(r'目前畫面時間：[^。]*。',f'目前畫面時間：{stamp(s["start"])}–{stamp(s["end"])}。',block,count=1)
        rows=[]
        for c in s['cues']:
            n+=1;rows.append(f'| {n:03} | {stamp(s["start"]+s["lead"]+c["start"])} | {stamp(s["start"]+s["lead"]+c["end"])} | {c["text"].strip()} |')
        block=re.sub(r'(?:^\| \d{3} \|[^\n]*\n)+','\n'.join(rows)+'\n',block,count=1,flags=re.M)
        parts[j+1]=block
    updated=''.join(parts)
    note='| 2026-10-05 | 採用使用者選定的 D 聲音（HsiaoChen +5%）；文字保留，依新配音更新分句與時間碼。 |\n'
    if note not in updated:updated+=note
    DOC.write_text(updated,encoding='utf-8')
    (OUT/'字幕與旁白.md').write_text(updated,encoding='utf-8')
    print('Editing MD updated:',n,'captions',flush=True)

async def main():
    raw=validate_editing_doc();sem=asyncio.Semaphore(3)
    segs=await asyncio.gather(*(synth(s,sem) for s in old['segments']))
    offset=0
    for s in segs:
        s['lead']=1.2 if s['id']==0 else .3
        s['duration']=math.ceil((s['speech_end']+1.4)*30)/30+(0.9 if s['id']==0 else 1.5 if s['id']==9 else 0)
        s['start']=offset;offset+=s['duration'];s['end']=offset
        s['cues']=captions(s)
    assert offset<=178
    data=dict(voice=VOICE,rate=RATE,duration=offset,cuts=copy.deepcopy(old['cuts']),segments=segs,narration_note='依使用者選擇換聲；沿用前版文字及第一項刪減，沒有新增刪減。')
    timeline=OUT/'timeline.json';timeline.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    entries=[]
    for s in segs:
        for c in s['cues']:
            entries.append(f'{len(entries)+1}\n{stamp(s["start"]+s["lead"]+c["start"],True)} --> {stamp(s["start"]+s["lead"]+c["end"],True)}\n{c["text"]}\n')
    (OUT/'scene_animation.srt').write_text('\n'.join(entries),encoding='utf-8-sig')
    print('Timeline ready:',round(offset,3),'seconds;',len(entries),'captions',flush=True)
    env=os.environ.copy();env.update(ANIMATION_OUTPUT=str(OUT),ANIMATION_ASSETS=str(ASSETS),ANIMATION_TIMELINE=str(timeline))
    for script,args in [('render.py',[]),('verify.py',[])]:
        subprocess.run([sys.executable,'-u',str(ROOT/script),*args],env=env,check=True)
    update_doc(raw,data)
    print('COMPLETE',str(OUT),flush=True)

if __name__=='__main__':asyncio.run(main())
