// 网页质检：控制台错误 + 横向溢出 + 残留 TeX/占位符 + 桌面/手机/展开/深色整页截图（自动切段，便于逐张查看）
// 用法：node qa.js <html路径> <输出目录> [--no-mobile] [--no-dark] [--seg 1500]
// 依赖：playwright（npm 包）+ 系统 chromium（自动用 `which chromium`；或设 CHROMIUM=/path）
const fs = require('fs'), path = require('path'), cp = require('child_process');
function loadPW() { const cands = [process.cwd(), __dirname, '/data', '/vercel/sandbox', process.env.NODE_PATH || ''];
  try { cands.push(cp.execSync('npm root -g').toString().trim()); } catch (e) {}
  for (const c of cands) { if (!c) continue; try { return require(require.resolve('playwright', { paths: [c] })); } catch (e) {} }
  throw new Error('找不到 playwright：在有 node_modules 的目录运行，或设置 NODE_PATH'); }
const { chromium } = loadPW();
const args = process.argv.slice(2); const file = path.resolve(args[0]); const out = path.resolve(args[1] || 'qa_out');
const SEG = +(args.includes('--seg') ? args[args.indexOf('--seg') + 1] : 1500);
fs.mkdirSync(out, { recursive: true });
function exe() { if (process.env.CHROMIUM) return process.env.CHROMIUM; for (const c of ['chromium', 'chromium-browser', 'google-chrome']) { try { return cp.execSync('which ' + c).toString().trim(); } catch (e) {} } return undefined; }
async function shoot(b, name, opt) {
  const p = await b.newPage({ viewport: { width: opt.w, height: 900 }, colorScheme: opt.dark ? 'dark' : 'light', deviceScaleFactor: 1 });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto('file://' + file); await p.waitForTimeout(800);
  if (opt.open) await p.evaluate(() => document.querySelectorAll('details').forEach(d => d.open = true));
  await p.waitForTimeout(300);
  const ovf = await p.evaluate(() => { const W = document.documentElement.clientWidth, out = [];
    document.querySelectorAll('body *').forEach(e => { const r = e.getBoundingClientRect(); if (r.right > W + 1 && r.width > 0) {
      let a = e.parentElement, clip = false; while (a) { const cs = getComputedStyle(a); if (/(auto|scroll|hidden|clip)/.test(cs.overflowX)) { if (a.getBoundingClientRect().right <= W + 1) { clip = true; break; } } a = a.parentElement; }
      if (!clip) out.push(e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ').join('.') : '') + ' → ' + (e.textContent || '').trim().slice(0, 30)); } });
    return { W, scrollW: document.documentElement.scrollWidth, items: out.slice(0, 20) }; });
  const lint = await p.evaluate(() => ({
    tex: [...document.querySelectorAll('.m,.mb')].filter(e => /\\[A-Za-z]/.test(e.innerText)).map(e => e.getAttribute('aria-label') || e.innerText).slice(0, 10),
    ph: (document.body.innerText.match(/\{\{[^}]{0,30}\}\}/g) || []).slice(0, 10) }));
  const full = path.join(out, name + '_full.png'); await p.screenshot({ path: full, fullPage: true });
  const H = await p.evaluate(() => document.documentElement.scrollHeight);
  await p.close();
  return { name, errs, ovf, full, H, lint };
}
(async () => {
  const b = await chromium.launch({ executablePath: exe() });
  const runs = [{ n: 'desktop', w: 1280 }, { n: 'desktop_open', w: 1280, open: true }];
  if (!args.includes('--no-mobile')) runs.push({ n: 'mobile_open', w: 390, open: true });
  if (!args.includes('--no-dark')) runs.push({ n: 'dark', w: 1280, dark: true });
  const report = [];
  for (const r of runs) report.push(await shoot(b, r.n, r));
  await b.close();
  // 切段（需要 python3 + Pillow）
  for (const r of report) {
    try { cp.execSync(`python3 -c "
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
im=Image.open('${r.full}'); W,H=im.size; n=0
for y in range(0,H,${SEG}):
    im.crop((0,y,W,min(H,y+${SEG}))).save('${path.join(out, r.name)}_%02d.png'%n); n+=1
print(n)"`); } catch (e) { console.log('切段失败（缺 Pillow？）', e.message); }
  }
  for (const r of report) {
    console.log(`[${r.name}] 高度 ${r.H}px；JS 错误 ${r.errs.length}${r.errs.length ? '：' + r.errs.join(' | ') : ''}；横向溢出 ${r.ovf.scrollW > r.ovf.W ? '有' : '无'}（${r.ovf.W}/${r.ovf.scrollW}）`);
    r.ovf.items.forEach(x => console.log('   溢出元素：' + x));
    if (r.name === 'desktop') {
      console.log(`   未支持的 TeX 命令（公式里残留反斜杠）：${r.lint.tex.length ? r.lint.tex.join(' | ') : '无'}`);
      console.log(`   未替换的占位符 {{…}}：${r.lint.ph.length ? r.lint.ph.join(' ') : '无'}`); }
  }
  console.log('截图目录：' + out);
})();
