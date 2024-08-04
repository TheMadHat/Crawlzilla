const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://techcrunch.com');
  console.log(await page.title());
  await browser.close();
})();
