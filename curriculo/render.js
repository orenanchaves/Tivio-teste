const { chromium } = require('playwright');
const path = require('path');
const DIR = '/home/user/Tivio-teste/curriculo/';
const JOBS = [
  ['CV_Renata_Xavier.html', 'Renata Xavier - Currículo.pdf'],
  ['CV_Renata_Xavier_XP.html', 'Renata Xavier - Currículo XP.pdf'],
];
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
  const p = await b.newPage();
  for (const [src, out] of JOBS) {
    await p.goto('file://' + path.join(DIR, src), { waitUntil: 'load' });
    await p.pdf({ path: path.join(DIR, out), format: 'Letter', printBackground: true, preferCSSPageSize: true });
    console.log('ok ->', out);
  }
  await b.close();
})();
