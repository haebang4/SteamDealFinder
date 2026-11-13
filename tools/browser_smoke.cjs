// Optional browser QA: npm install playwright, then node tools/browser_smoke.cjs
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1360, height: 1000 } });
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(path.resolve('data/demo/index.html')).href);
    if (await page.locator('#inversions tr').count() !== 1) throw Error('Missing demo inversion');
    if (!(await page.locator('#inversions').innerText()).includes('94.06%')) throw Error('Wrong inversion');
    if (await page.locator('#products tr').count() !== 2) throw Error('Missing unfiltered products');
    if (!(await page.locator('#products').innerText()).includes('30,000원')) throw Error('Missing original price');
    if (!(await page.locator('#products').innerText()).includes('3,000원')) throw Error('Missing current price');
    if (await page.locator('a[href="all_products.csv"]').count() !== 1) throw Error('Missing all-product download');
    await page.locator('#query').fill('no-such-game');
    if (!(await page.locator('#deals').innerText()).includes('표시할 결과가 없습니다')) throw Error('Search failed');
    await page.locator('#query').fill('');
    await page.locator('#price').fill('1000');
    if (!(await page.locator('#inversions').innerText()).includes('표시할 결과가 없습니다')) throw Error('Price filter failed');
    await page.locator('#price').fill('');
    await page.locator('#discount').fill('95');
    if (!(await page.locator('#inversions').innerText()).includes('표시할 결과가 없습니다')) throw Error('Discount filter failed');
    await page.locator('#discount').fill('0');
    await page.evaluate(() => { data.deals.push({ ...data.deals[0], name: '가나다 sort fixture', price: 4500, discount: 99 }); render(); });
    if (!(await page.locator('#deals tr').first().innerText()).includes('가나다 sort fixture')) throw Error('Discount sort failed');
    await page.locator('#sort').selectOption('price');
    if ((await page.locator('#deals tr').first().innerText()).includes('가나다 sort fixture')) throw Error('Price sort failed');
    await page.locator('#sort').selectOption('name');
    if (!(await page.locator('#deals tr').first().innerText()).includes('가나다 sort fixture')) throw Error('Name sort failed');
    await page.evaluate(() => { data.deals.pop(); render(); });
    fs.mkdirSync('data/qa', { recursive: true });
    await page.screenshot({ path: 'data/qa/demo-desktop.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: 'data/qa/demo-mobile.png', fullPage: true });
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) throw Error('Mobile page overflow');
    await page.setViewportSize({ width: 1360, height: 1000 });
    await page.goto(pathToFileURL(path.resolve('docs/index.html')).href);
    await page.screenshot({ path: 'data/qa/live-desktop.png', fullPage: true });
    if (errors.length) throw Error(errors.join('\n'));
    console.log('Browser checks passed: rendering, search, price/discount filters, sort, mobile width, no JS errors.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });

