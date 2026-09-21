const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.goto('file:///home/user/Tivio-teste/curriculo/CV_Renata_Xavier.html', { waitUntil: 'load' });
  await p.pdf({
    path: '/home/user/Tivio-teste/curriculo/CV_Renata_Xavier.pdf',
    format: 'Letter',
    printBackground: true,
    preferCSSPageSize: true,
  });
  await b.close();
})();
