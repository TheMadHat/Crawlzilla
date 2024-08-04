// https://www.engadget.com/best-wireless-earbuds-120058222.html
// 7ea475da-d873-4651-addc-8892b52fc58b
// f3717be3-a7e9-4132-a8b5-fa2fc4bc949d
// df632b40-685f-46a2-9969-e303cafe8a52
// 1e17bc15-28a6-4e95-a46f-b57aca7c45d1
// c31f22ca-1bf2-4903-afc2-1784cc15cf9f
// 500dc413-5aef-4603-a5f8-6ad0e1d8d0fb
// 36e1c617-1fbd-43a4-9ae3-84fd9bd1993e
// e79d01d7-bba1-4bdb-a0bb-621662c50db0
// a685378e-d6a8-4dfd-a0ec-4c3a8d614bdc

const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();

    const targetDivIds = ['HeadlineSection'];
  const targetDivClasses = ['caas-jump-link-heading'];
  const targetInsideATags = ['a.7ea475da-d873-4651-addc-8892b52fc58b', 'a.f3717be3-a7e9-4132-a8b5-fa2fc4bc949d','a.df632b40-685f-46a2-9969-e303cafe8a52', 'a.1e17bc15-28a6-4e95-a46f-b57aca7c45d1','a.c31f22ca-1bf2-4903-afc2-1784cc15cf9f', 'a.500dc413-5aef-4603-a5f8-6ad0e1d8d0fb','a.36e1c617-1fbd-43a4-9ae3-84fd9bd1993e', 'a.e79d01d7-bba1-4bdb-a0bb-621662c50db0','a.a685378e-d6a8-4dfd-a0ec-4c3a8d614bdc'];
  const url = 'https://www.engadget.com/best-wireless-earbuds-120058222.html';

  await page.goto(url);

  try {
    const loadTimes = {};

      for (const id of targetDivIds) {
      await page.waitForSelector(`#${id}`, { timeout: 60000 });
      loadTimes[`#${id}`] = await page.evaluate(() => performance.now());
    }

      for (const className of targetDivClasses) {
      await page.waitForSelector(`.${className}`, { timeout: 60000 });
      loadTimes[`.${className}`] = await page.evaluate(() => performance.now());
    }

      for (const selector of targetInsideATags) {
      await page.waitForSelector(selector, { timeout: 60000 });
      loadTimes[selector] = await page.evaluate(() => performance.now());
    }

      const performanceTiming = await page.evaluate(() => {
      const navTiming = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: navTiming.domContentLoadedEventEnd,
        loadEventEnd: navTiming.loadEventEnd
      };
    });

    console.log(`DOM Content Loaded: ${performanceTiming.domContentLoaded}ms`);
    console.log(`Page Load Event End: ${performanceTiming.loadEventEnd}ms`);
    
    for (const [selector, time] of Object.entries(loadTimes)) {
      console.log(`Time to load ${selector}: ${time}ms`);
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
  } finally {
    await browser.close();
  }
})();
