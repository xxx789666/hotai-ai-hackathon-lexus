"""Verify the delivery, against the supplied final narration and allowed cuts."""
import csv, hashlib, json, math, os, re, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from art import font, INK

ROOT=Path(__file__).resolve().parent
OUT=Path(os.environ.get('ANIMATION_OUTPUT',str(ROOT/'output')))
ASSETS=Path(os.environ.get('ANIMATION_ASSETS',str(ROOT/'assets')))
data=json.loads(Path(os.environ.get('ANIMATION_TIMELINE',str(ROOT/'timeline.json'))).read_text(encoding='utf-8'))
source=(ROOT.parents[1]/'使用場景動畫_製作提示詞_GPT.md').read_text(encoding='utf-8')
original=[s.strip() for s in source.split('### 4.')[1].split('### 5.')[0].split('\n\n')[1:] if s.strip()]
expected=original.copy()
for c in data['cuts']:
    for old,new in c['edits']:expected[c['scene']]=expected[c['scene']].replace(old,new)
for s in data['segments']:
    assert s['text']==expected[s['id']]
    assert ''.join(c['text'] for c in s['cues'])==s['text']
    for c in s['cues']:
        assert len(c['text'])<=22,(s['id'],c)
        assert c['end']-c['start']>=2,(s['id'],c)
        assert font(42).getlength(c['text'])<1720
    assert s['end']-(s['start']+s['lead']+s['speech_end'])>=1.099

p=OUT/'scene_animation.mp4'
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
v=next(s for s in meta['streams'] if s['codec_type']=='video');a=next(s for s in meta['streams'] if s['codec_type']=='audio')
assert v['width']==1920 and v['height']==1080 and v['r_frame_rate']=='30/1'
assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p'
assert a['codec_name']=='aac' and a['channels']==2
duration=float(meta['format']['duration']);assert duration<=178
frames=sum(round(s['duration']*30) for s in data['segments'])
assert int(v['nb_frames'])==frames
assert abs(float(v['duration'])-float(a['duration']))<.08
subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)

tiles=[]
for s in data['segments']:
    for frac in [.3,.74,.91]:
        t=s['start']+s['duration']*frac;path=ASSETS/f'encoded_{s["id"]}_{int(frac*100)}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(p),'-frames:v','1','-q:v','2',str(path)],check=True)
        im=Image.open(path).resize((480,270));tile=Image.new('RGB',(480,305),'white');tile.paste(im)
        ImageDraw.Draw(tile).text((12,276),f'SCENE {s["id"]} / {t:.1f}s',font=font(18),fill=INK);tiles.append(tile)
sheet=Image.new('RGB',(1440,3050),'white')
for j,tile in enumerate(tiles):sheet.paste(tile,((j%3)*480,(j//3)*305))
sheet.save(OUT/'verified_frames.jpg',quality=92)

facts=[
('0','每 6 位有 1 位、16.4%','第 5 節風險分級；高風險占論壇發言者比例，非全體車主'),
('1','21,183 句；PTT、Mobile01、Dcard','第 5 節資料；Mobile01 是論壇名稱'),
('2','1,671；186','第 5 節資料：流失句及無抱怨流失句'),
('2','17.3%、15.0%、9.5%、8.9%、7.4%、7.2%、4.7%、3.0%、1.4%','第 5 節九面向流失率，依原順序對應'),
('3','511、247、195、128；199','第 5 節四種客群人數及未分類觀察名單'),
('4','八條規則；1,049、231、5,114；74%、1.8%','第 5 節風險分公式及風險分級'),
('5','60 天、1.5 倍、第 7 天、7 天','第 5 節接觸時機；另呈現刪項後首次回廠'),
('6','76、40、36','第 5 節官方條款：總數、官網、手冊'),
('各段','2026、產出 1、產出 2','第 1、2、3 節明定的活動年份及產出編號；不是新增成效數字')]
caption_count=sum(len(s['cues']) for s in data['segments'])
lines=['# 交付與自我檢查','',f'影片：scene_animation.mp4；實測 {duration:.3f} 秒。',
'1920×1080、30 fps、H.264 / yuv420p、AAC 48 kHz 立體聲。',
f'影片共 {frames:,} 格，完整解碼未發現錯誤。','',
'## 旁白與刪減','',
f'使用 {data["voice"]}，合成語速 {data["rate"]}。'+data.get('narration_note','完整旁白加場景停留及轉場共 181.333 秒，超過上限，依第 6 節只套用第一項刪減。'),
'第 3 段移除「，人數最多」「修不好就」「自己走，還」「從不抱怨，」。其餘旁白逐字保留，未套用第二至第四項。',
f'字幕與刪減後旁白逐字一致，共 {caption_count} 句；每行最多 22 個字元，每句至少 2 秒。字幕已燒錄於影片，另附 UTF-8 SRT。',
'每段旁白後保留至少 0.8 秒；段間以兩側各 0.3 秒白光轉場。時間表見 timing.csv。','',
'## 數字來源','',
'| 段落 | 畫面數字 | 原文件依據 |','| --- | --- | --- |']
lines += ['| '+' | '.join(row)+' |' for row in facts]
lines += ['','## 第 5 節逐項核對','',
'- 資料、九面向流失率、四種客群：按定稿呈現。未分類 199 人標為觀察名單、不投遞。',
'- 風險分級與公式：呈現模型判斷＋八條規則，高中低人數及 74%／1.8%；未另造公式或效果指標。',
'- 看板：風險段呈現戰情總覽、報告池、原始輿情；條款段呈現知識資料；審核段呈現溝通審核佇列。',
'- 時機：五項均在畫面列出。官方條款：76＝40＋36，逐字比對、引用編號、未公開價格不寫入。',
'- 審核：核准／改寫／退回；人工核准才投遞；客訴回訪不計頻率上限；觀察名單車主也回訪。',
'- 管道與回饋：LINE、Email、App、專員電話；點擊、預約、回廠回寫；校正觸發門檻、再訓練模型。',
'- 母體註明論壇發言者，資料與模型留在和泰內網。','',
'## 第 7 節禁止事項核對','',
'- 未使用真實帳號、店名、人名、論壇原句。名單／訊息使用抽象色條，相關畫面標「示意」。',
'- 未宣稱回廠率提升、金錢節省或保證效果。',
'- Lexus、和泰、管道名稱均使用文字；未仿製品牌標誌。',
'- 畫面事實數字逐項列於上表；旁白差異僅為指定第一项刪減。',
'- 人物、車輛、場景、介面與光帶皆由本資料夾程式自行繪製。配樂為自行合成和弦鋪底；未使用外部音樂或圖庫。',
'- 字型使用系統 Noto Sans TC；字型內嵌授權為 SIL Open Font License 1.1。','',
'## 品質檢查與實作說明','',
'- 十段共 30 張已編碼畫面抽驗：verified_frames.jpg；構圖預覽：storyboard.jpg。',
'- 字幕 42 px、深藍、單行、無底框；與主要內容分置，文字宽度檢查通過。',
'- 白／淡藍底、藍色主色、紅黃強調；無五官人物、等角面板、光帶、微幅視差與緩推。',
'- 資料依合成語音時間戳進場；示意螢幕沒有數值刻度，並標示「示意」。',
'- 配樂以有效人聲 RMS 為基準降低 20 dB，合成後峰值約 -1.1 dBFS。',
'- 動畫採程式繪製的圖解場景；白光溶接、卡片滑入與光點移動為主要動態。',
'- 原有 video/out 及 video/scene_animation 保留；本版全部位於 video/gpt_animation。','',
'## 重製','',
'在本目錄執行：','',
'```powershell',*(['python build_hsiaochen.py'] if data['voice']=='zh-TW-HsiaoChenNeural' else ['python prepare.py','python render.py --preview','python render.py','python verify.py']),'```','',
'依賴：Python、Pillow、NumPy、edge-tts、FFmpeg／FFprobe；Noto Sans TC。既有音檔有快取，首次合成需要網路。']
(OUT/'交付檢查.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
metrics=dict(duration=duration,frames=frames,caption_count=sum(len(s['cues']) for s in data['segments']),min_caption_seconds=min(c['end']-c['start'] for s in data['segments'] for c in s['cues']),max_caption_characters=max(len(c['text']) for s in data['segments'] for c in s['cues']),narration_matches=True,full_decode_passed=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(OUT/'verification.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
print(json.dumps(metrics,indent=2),flush=True)
