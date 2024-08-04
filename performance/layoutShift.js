const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();

  const url = 'https://www.engadget.com/best-wireless-earbuds-120058222.html';  // Replace with the actual URL
  await page.goto(url);

  // Use PerformanceObserver to capture LayoutShift entries
  const layoutShiftMetrics = await page.evaluate(() => {
    return new Promise((resolve) => {
      const layoutShifts = [];

      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.entryType === 'layout-shift' && !entry.hadRecentInput) {
            layoutShifts.push({
              value: entry.value,
              sources: entry.sources.map(source => ({
                node: source.node ? source.node.nodeName : null,
                previousRect: source.previousRect,
                currentRect: source.currentRect
              }))
            });
          }
        });
      });

      observer.observe({ type: 'layout-shift', buffered: true });

      // Ensure the observer has time to capture entries
      setTimeout(() => {
        resolve(layoutShifts);
      }, 5000);  // Increased wait time to capture entries
    });
  });

  // Log layout shift metrics to the console
  console.log('Layout Shift Metrics:', JSON.stringify(layoutShiftMetrics, null, 2));

  await browser.close();
})();
