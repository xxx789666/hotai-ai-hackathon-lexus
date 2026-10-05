/* common.js：三個場景共用的「逐格決定論」動畫引擎。
 *
 * 用法：場景 HTML 載入本檔後，呼叫 Scene.init({defaults}) 讀 URL 參數：
 *   T        場景總長（秒）
 *   lead     旁白開始時間（秒）；所有以旁白為準的節拍 key 都加上 lead
 *   k_xxx    節拍時間（旁白內相對秒數，由 render.py 從 tts_timing.json 帶入）
 *   in / out 進場／出場轉場種類：none | sweep | glow，以及 din / dout 轉場秒數
 * 然後呼叫 Scene.seek(t)：根據 t（秒）把畫面一次算到位（不用 requestAnimationFrame）。
 * render.py 逐格 seek 後截圖；瀏覽器直接開啟時會自動播放預覽（也是逐格 seek）。
 */
const Scene = (() => {
  const P = new URLSearchParams(location.search);
  const num = (k, d) => (P.has(k) ? parseFloat(P.get(k)) : d);
  const S = { T: 15, lead: 1.0, din: 0.6, dout: 0.6, in: 'none', out: 'none', keys: {}, cues: [], tweens: [], floats: [], hooks: [], inits: [] };

  // ---- 緩動 ----
  const E = {
    linear: p => p,
    out: p => 1 - Math.pow(1 - p, 3),
    in: p => p * p * p,
    inout: p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    back: p => { const c1 = 1.20158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
    smooth: p => p * p * (3 - 2 * p),
  };
  const clamp01 = x => (x < 0 ? 0 : x > 1 ? 1 : x);
  const prog = (t, at, dur, e = 'out') => E[e](clamp01((t - at) / (dur || 0.0001)));
  const lerp = (a, b, p) => a + (b - a) * p;
  const mix = (a, b, p) => { const o = {}; for (const k in b) o[k] = lerp(a[k] ?? b[k], b[k], p); for (const k in a) if (!(k in o)) o[k] = a[k]; return o; };

  // ---- 決定論亂數（mulberry32）----
  function rng(seed) {
    let a = seed >>> 0;
    return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  // ---- 宣告式 tween ----
  // tween(sel, at, dur, to, {from, e}): 時間 at 起、歷時 dur，把 sel 的狀態從 from（或目前）插值到 to。
  // 狀態欄位：x y（px 位移）s（縮放）sx sy（單軸縮放）r（旋轉度）o（透明度）w（寬 px）。
  function tween(sel, at, dur, to, opt = {}) {
    const els = typeof sel === 'string' ? [...document.querySelectorAll(sel)] : [sel];
    S.tweens.push({ els, at, dur, to, from: opt.from, e: opt.e || 'out', stagger: opt.stagger || 0 });
    return S;
  }
  // 漂浮：在 tween 之後疊加正弦位移
  function float(sel, amp = 6, period = 4, phase = 0, axis = 'y') {
    const els = typeof sel === 'string' ? [...document.querySelectorAll(sel)] : [sel];
    els.forEach((el, i) => S.floats.push({ el, amp, period, phase: phase + i * 0.9, axis }));
    return S;
  }
  function hook(fn) { S.hooks.push(fn); return S; }

  const DEFAULT = { x: 0, y: 0, s: 1, sx: 1, sy: 1, r: 0, o: 1 };
  const FIGURE = `<circle class="skin" cx="50" cy="30" r="20"/>
      <path class="hair" d="M30 28 a20 20 0 0 1 40 0 v5 a20 20 0 0 1 -40 0z"/>
      <path class="cloth" d="M24 96 v-28 a26 26 0 0 1 52 0 v28z"/>
      <path class="shirt" d="M44 68 h12 l-6 20z"/>`;
  function applyState(el, st) {
    const base = el.dataset.base || '';
    el.style.transform = `translate(${st.x}px,${st.y}px) ${base} rotate(${st.r}deg) scale(${st.s * st.sx},${st.s * st.sy})`;
    el.style.opacity = st.o;
    if ('w' in st) el.style.width = st.w + 'px';
  }

  function applyTweens(t) {
    const state = new Map();
    // 有 data-init 的元素先套初始狀態（例如 o:0），避免 tween 尚未開始時以原始 CSS 狀態露出
    for (const el of S.inits) state.set(el, { ...DEFAULT, ...el.__init });
    for (const tw of S.tweens) {
      tw.els.forEach((el, i) => {
        const at = tw.at + i * tw.stagger;
        if (t < at && !tw.from) return;
        const cur = state.get(el) || { ...DEFAULT, ...(el.__init || {}) };
        const from = tw.from ? { ...cur, ...tw.from } : cur;
        const p = prog(t, at, tw.dur, tw.e);
        state.set(el, mix(from, { ...from, ...tw.to }, p));
      });
    }
    for (const f of S.floats) {
      const st = state.get(f.el) || { ...DEFAULT, ...(f.el.__init || {}) };
      st[f.axis] += Math.sin((t / f.period) * Math.PI * 2 + f.phase) * f.amp;
      state.set(f.el, st);
    }
    for (const [el, st] of state) applyState(el, st);
  }

  // ---- 字幕 ----
  function subtitle(t) {
    const box = document.getElementById('subtitle');
    if (!box) return;
    const tt = t - S.lead;
    const c = S.cues.find(c => tt >= c.start && tt < c.show_end);
    box.textContent = c ? c.text : '';
  }

  // ---- 轉場（光掃／大光暈），畫在最上層 ----
  function transitions(t) {
    const sw = document.getElementById('sweep');
    const gl = document.getElementById('glow');
    if (!sw || !gl) return;
    sw.style.opacity = 0; gl.style.opacity = 0;
    // 出場：最後 dout 秒；進場：最前 din 秒
    let kind = null, p = 0;
    if (S.out !== 'none' && t >= S.T - S.dout) { kind = S.out; p = 0.5 * clamp01((t - (S.T - S.dout)) / S.dout); }
    else if (S.in !== 'none' && t < S.din) { kind = S.in; p = 0.5 + 0.5 * clamp01(t / S.din); }
    if (!kind) return;
    if (kind === 'sweep') {
      // 光帶從左掃到右（p 0→1 橫跨前後兩個場景），帶後方為白色薄紗
      const x = lerp(-900, 1920 + 900, E.inout(p));
      sw.style.opacity = 1;
      sw.style.setProperty('--sx', x + 'px');
      // 白紗：出場時 band 之後漸白；進場時 band 之後顯露
      const veil = sw.querySelector('.veil');
      // 出場：band 之後 1000px 內全白（切點時整幅已白）；進場：band 之前 1000px 起全白
      if (p < 0.5) { veil.style.left = '-2000px'; veil.style.width = (x + 2000 + 1000) + 'px'; }
      else { veil.style.left = (x - 1000) + 'px'; veil.style.width = '5000px'; }
    } else if (kind === 'glow') {
      const q = p < 0.5 ? E.in(p * 2) : 1 - E.out((p - 0.5) * 2);
      gl.style.opacity = 1;
      gl.style.setProperty('--gs', (0.05 + q * 3.2));
      gl.style.setProperty('--go', Math.min(1, q * 1.6));
    }
  }

  function seek(t) {
    S.t = t;
    applyTweens(t);
    for (const h of S.hooks) h(t);
    subtitle(t);
    transitions(t);
  }

  function init(defaults = {}) {
    S.T = num('T', defaults.T ?? S.T);
    S.lead = num('lead', defaults.lead ?? S.lead);
    S.din = num('din', defaults.din ?? S.din);
    S.dout = num('dout', defaults.dout ?? S.dout);
    S.in = P.get('in') || defaults.in || 'none';
    S.out = P.get('out') || defaults.out || 'none';
    for (const [k, v] of Object.entries(defaults.keys || {})) S.keys[k] = S.lead + num(k, v);
    for (const [k, v] of P) if (k.startsWith('k_') && !(k in S.keys)) S.keys[k] = S.lead + parseFloat(v);
    // cues：render.py 以 window.CUES 注入；直接開檔時用 defaults.cues 預覽
    S.cues = window.CUES || defaults.cues || [];
    // 無五官人形：把 <svg data-fig class="fig owner"> 填入圖形（不用 <use>，讓 CSS 服裝色能套用）
    document.querySelectorAll('svg[data-fig]').forEach(el => {
      el.setAttribute('viewBox', '0 0 100 100');
      el.innerHTML = FIGURE;
    });
    // 記錄元素初始狀態（data-init="x:10,o:0"）
    S.inits = [...document.querySelectorAll('[data-init]')];
    S.inits.forEach(el => {
      const o = {}; el.dataset.init.split(',').forEach(kv => { const [k, v] = kv.split(':'); o[k.trim()] = parseFloat(v); }); el.__init = o;
    });
    return S;
  }

  // 直接在瀏覽器開啟：自動逐格預覽（非決定論的只有「現在時間」，畫面本身仍由 t 決定）
  function preview() {
    if (window.__RENDER__) return;
    const t0 = performance.now();
    const loop = () => { const t = ((performance.now() - t0) / 1000) % S.T; seek(t); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  }

  return { S, init, seek, tween, float, hook, rng, prog, lerp, E, clamp01, preview, fmt: n => n.toLocaleString('en-US') };
})();
window.Scene = Scene;
window.seek = t => Scene.seek(t);
