// Regenerates the Open Graph image (1200x627 PNG) from src/*.html.
// Usage (from anywhere):  node docs/assets/og/render.js
// Needs Playwright with a browser installed:  npm i -D playwright && npx playwright install firefox
const path = require('path');
const { firefox } = require('playwright');
const W = 1200, H = 627;
const pages = ['og-tuxsign'];
(async () => {
  const browser = await firefox.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  for (const name of pages) {
    await page.goto('file://' + path.join(__dirname, 'src', name + '.html'));
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(__dirname, name + '.png'), clip: { x: 0, y: 0, width: W, height: H } });
    console.log('rendered', name + '.png');
  }
  await browser.close();
})();
