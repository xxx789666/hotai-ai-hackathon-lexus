import argparse, concurrent.futures, csv, json, math, os, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import Art, W,H,BLUE,INK,MUTED,font,make_scene,background

ROOT=Path(__file__).resolve().parent
OUT=Path(os.environ.get('ANIMATION_OUTPUT',str(ROOT/'output')))
ASSETS=Path(os.environ.get('ANIMATION_ASSETS',str(ROOT/'assets')))
for folder in [OUT,ASSETS]:folder.mkdir(parents=True,exist_ok=True)
TIMELINE=json.loads(Path(os.environ.get('ANIMATION_TIMELINE',str(ROOT/'timeline.json'))).read_text(encoding='utf-8'))
FPS=30

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def ribbon():
    points=[]
    for j in range(301):
        u=j/300
        x=-70+2070*u
        y=805-180*math.sin(u*math.pi*2-.6)-70*u
        points.append((x,y))
    a=Image.new('RGBA',(W,H));d=ImageDraw.Draw(a)
    d.line(points,fill=(99,155,225,70),width=38)
    a=a.filter(ImageFilter.GaussianBlur(20));d=ImageDraw.Draw(a)
    d.line(points,fill=(143,183,234,105),width=13)
    a=a.filter(ImageFilter.GaussianBlur(3));d=ImageDraw.Draw(a)
    d.line(points,fill=(255,255,255,220),width=4)
    return a,points

class Scene:
    def __init__(self,s):
        self.s=s;self.layers=make_scene(s);self.bg=background();self.ribbon,self.path=ribbon()
        self.bg.alpha_composite(self.ribbon)
        self.captions=[]
        for c in s['cues']:
            a=Art();a.text(W/2,981,c['text'],42,INK,False,anchor='mt')
            im=a.finish();bb=im.getbbox()
            self.captions.append((c,im.crop(bb),bb))
        self.white=Image.new('RGB',(W,H),'white')
        yy,xx=np.mgrid[0:H,0:W]
        self.bloom=Image.fromarray((np.exp(-((xx-980)**2/650**2+(yy-515)**2/425**2))*255).astype('uint8'))
        self.night=Image.new('RGB',(W,H),'#182A46');d=ImageDraw.Draw(self.night)
        for j in range(120):
            x=(j*761+97)%W;y=(j*317+71)%H;r=1+(j%3)
            d.ellipse((x-r,y-r,x+r,y+r),fill=['#6281A6','#A4BAD5','#DCE8F5'][j%3])

    def frame(self,t):
        s=self.s;im=self.bg.copy();d=ImageDraw.Draw(im)
        for k in range(7):
            u=((s['start']+t)*.027+k/7)%1
            x,y=self.path[round(u*300)];r=3+(k%2)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255,240))
        for n,l in enumerate(self.layers):
            age=t-l['t'];alpha=smooth(age/.85)
            if l['exit'] is not None:alpha*=1-smooth((t-l['exit'])/.4)
            if alpha<=0:continue
            drift=l['drift'];dx=math.sin(t*.5+n*.8)*4*drift
            dy=math.sin(t*.8+n*.9)*4*drift+(1-smooth(age/.95))*38
            layer=l['im']
            if alpha<.999:
                layer=layer.copy();layer.putalpha(layer.getchannel('A').point(lambda a:int(a*alpha)))
            im.alpha_composite(layer,(round(l['x']+dx),round(l['y']+dy)))
        # A slow push, with a new gentle camera beat every five seconds.
        push=.0025*(1-math.cos(t*math.pi/5))
        if push:
            nw=round(W*(1+push));nh=round(H*(1+push))
            im=im.resize((nw,nh),Image.Resampling.BILINEAR).crop(((nw-W)//2,(nh-H)//2,(nw+W)//2,(nh+H)//2))
        for c,cap,bb in self.captions:
            if c['start']<=t-s['lead']<c['end']:
                im.alpha_composite(cap,(bb[0],bb[1]));break
        im=im.convert('RGB')
        if s['id']==0 and t<1.45:im=Image.blend(self.night,im,smooth(t/1.45))
        # A single broader halo crossing between output 1 and output 2.
        halo=0
        if s['id']==4:halo=smooth((t-(s['duration']-.65))/.45)
        elif s['id']==5:halo=1-smooth(t/.65)
        if halo>0:
            mask=self.bloom.point(lambda v:round(min(255,v*halo*2.4)))
            im=Image.composite(self.white,im,mask)
        enter=1-smooth(t/.3) if s['id']>0 else 0
        leave=smooth((t-(s['duration']-.3))/.3) if s['id']<9 else 0
        fade=max(enter,leave)
        if fade>0:im=Image.blend(im,self.white,fade)
        return im

def render_segment(i):
    s=TIMELINE['segments'][i];scene=Scene(s);out=ASSETS/f'scene_{i}.mp4'
    frames=round(s['duration']*FPS)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    with (ASSETS/f'encode_{i}.log').open('wb') as log:
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        try:
            for f in range(frames):p.stdin.write(scene.frame(f/FPS).tobytes())
        finally:p.stdin.close()
        if p.wait()!=0:raise RuntimeError(f'encode failed {i}')
    return dict(scene=i,frames=frames,file=str(out))

def audio():
    rate=48000;n=round(TIMELINE['duration']*rate);voice=np.zeros(n,dtype=np.float32)
    for s in TIMELINE['segments']:
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',s['audio'],'-f','f32le','-ac','1','-ar',str(rate),'pipe:1'])
        v=np.frombuffer(raw,dtype=np.float32);start=round((s['start']+s['lead'])*rate)
        voice[start:min(n,start+len(v))]+=v[:n-start]
    # Original slow harmonic pad, synthesized from sine partials.
    pad=np.zeros((n,2),dtype=np.float32)
    chords=[[146.832,220,293.665,369.994],[130.813,196,261.626,329.628],[164.814,220,329.628,440],[146.832,220,293.665,440]]
    for j,start in enumerate(range(0,n,rate*10)):
        length=min(n-start,rate*13);t=np.arange(length,dtype=np.float32)/rate
        env=np.minimum(1,t/3)*np.minimum(1,(length/rate-t)/3)
        for k,f in enumerate(chords[j%4]):
            for ch in range(2):
                waveval=(np.sin(2*np.pi*(f+ch*.1)*t+k*.3)+.16*np.sin(2*np.pi*f*2*t+k))*.12
                pad[start:start+length,ch]+=waveval*env
    active=voice[np.abs(voice)>.01];vrms=float(np.sqrt(np.mean(active**2)))
    prms=float(np.sqrt(np.mean(pad**2)));pad*=vrms*.1/max(prms,1e-8)
    fade=np.minimum(1,np.arange(n,dtype=np.float32)/(rate*2))*np.minimum(1,np.arange(n,0,-1,dtype=np.float32)/(rate*3))
    pad*=fade[:,None]
    mix=voice[:,None]+pad
    peak=float(np.max(np.abs(mix)));gain=.88/max(peak,.01);mix*=gain
    with wave.open(str(ASSETS/'mix.wav'),'wb') as f:
        f.setparams((2,2,rate,n,'NONE','not compressed'));f.writeframes((mix*32767).clip(-32768,32767).astype('<i2').tobytes())
    (ASSETS/'audio_metrics.json').write_text(json.dumps(dict(voice_active_rms=vrms,pad_rms_target=vrms*.1,music_relative_db=-20,peak_dbfs=20*math.log10(float(np.max(np.abs(mix))))),indent=2),encoding='utf-8')

def previews():
    thumbs=[]
    for s in TIMELINE['segments']:
        scene=Scene(s)
        for fraction in [.3,.74]:
            t=s['duration']*fraction;frame=scene.frame(t)
            frame.save(ASSETS/f'preview_{s["id"]}_{int(fraction*100)}.jpg',quality=94)
            thumb=frame.resize((480,270),Image.Resampling.LANCZOS)
            tile=Image.new('RGB',(480,309),'#FFFFFF');tile.paste(thumb,(0,0))
            ImageDraw.Draw(tile).text((15,278),f'SCENE {s["id"]}  /  {s["start"]+t:.1f}s',font=font(18),fill=INK)
            thumbs.append(tile)
    sheet=Image.new('RGB',(1920,309*5),'#FFFFFF')
    for j,t in enumerate(thumbs):sheet.paste(t,((j%4)*480,(j//4)*309))
    sheet.save(OUT/'storyboard.jpg',quality=94)
    print('Preview ready',flush=True)

def package():
    concat=ASSETS/'concat.txt'
    concat.write_text('\n'.join(f"file 'scene_{i}.mp4'" for i in range(10)),encoding='utf-8')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(ASSETS/'mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t',str(TIMELINE['duration']),'-movflags','+faststart',str(OUT/'scene_animation.mp4')],check=True)
    with (OUT/'timing.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['段落','畫面起秒','畫面訖秒','旁白起秒','旁白訖秒','旁白秒數','原文'])
        for s in TIMELINE['segments']:writer.writerow([s['id'],round(s['start'],3),round(s['end'],3),round(s['start']+s['lead'],3),round(s['start']+s['lead']+s['speech_end'],3),round(s['speech_end'],3),s['text']])
    print('Packaged',OUT/'scene_animation.mp4',flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');parser.add_argument('--scenes');parser.add_argument('--package',action='store_true');args=parser.parse_args()
    if args.preview:previews();return
    if args.package:audio();package();return
    ids=[int(v) for v in args.scenes.split(',')] if args.scenes else list(range(10))
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(render_segment,i) for i in ids]
        for f in concurrent.futures.as_completed(futures):print('Rendered',f.result(),flush=True)
    if len(ids)==10:audio();package()

if __name__=='__main__':main()
