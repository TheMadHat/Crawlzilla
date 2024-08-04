const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();

  const url = 'https://www.engadget.com/best-wireless-earbuds-120058222.html';  // Replace with the actual URL
  await page.goto(url);

  const performanceTiming = await page.evaluate(() => {
    const navTiming = performance.getEntriesByType('navigation')[0];
    return {
      navigationStart: navTiming.navigationStart,
      fetchStart: navTiming.fetchStart,
      domainLookupStart: navTiming.domainLookupStart,
      domainLookupEnd: navTiming.domainLookupEnd,
      connectStart: navTiming.connectStart,
      secureConnectionStart: navTiming.secureConnectionStart,
      connectEnd: navTiming.connectEnd,
      requestStart: navTiming.requestStart,
      responseStart: navTiming.responseStart,
      responseEnd: navTiming.responseEnd,
      domLoading: navTiming.domLoading,
      domInteractive: navTiming.domInteractive,
      domContentLoadedEventStart: navTiming.domContentLoadedEventStart,
      domContentLoadedEventEnd: navTiming.domContentLoadedEventEnd,
      domComplete: navTiming.domComplete,
      loadEventStart: navTiming.loadEventStart,
      loadEventEnd: navTiming.loadEventEnd,
      type: navTiming.type,
      redirectCount: navTiming.redirectCount
    };
  });

  console.log(performanceTiming);

  await browser.close();
})();
