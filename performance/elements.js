const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();

  const url = 'https://www.engadget.com/best-wireless-earbuds-120058222.html';  // Replace with the actual URL
  await page.goto(url);

  // Use PerformanceObserver to capture various performance entries
  const performanceMetrics = await page.evaluate(() => {
    return new Promise((resolve) => {
      const elementTimings = [];
      const paintTimings = [];
      const largestContentfulPaintTimings = [];

      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.entryType === 'element') {
            elementTimings.push({
              renderTime: entry.renderTime,
              loadTime: entry.loadTime,
              identifier: entry.identifier,
              naturalWidth: entry.naturalWidth,
              naturalHeight: entry.naturalHeight,
              id: entry.id,
              url: entry.url,
              size: entry.size
            });
          } else if (entry.entryType === 'paint') {
            paintTimings.push({
              name: entry.name,
              startTime: entry.startTime
            });
          } else if (entry.entryType === 'largest-contentful-paint') {
            largestContentfulPaintTimings.push({
              renderTime: entry.renderTime,
              loadTime: entry.loadTime,
              size: entry.size,
              id: entry.id,
              url: entry.url,
              element: entry.element ? entry.element.tagName : null
            });
          }
        });
      });

      observer.observe({ type: 'element', buffered: true });
      observer.observe({ type: 'paint', buffered: true });
      observer.observe({ type: 'largest-contentful-paint', buffered: true });

      // Ensure the observer has time to capture entries
      setTimeout(() => {
        resolve({
          elementTimings,
          paintTimings,
          largestContentfulPaintTimings
        });
      }, 15000);  // Increased wait time to capture entries
    });
  });

  // Log performance metrics to the console
  console.log('Element Timing Metrics:', performanceMetrics.elementTimings);
  console.log('Paint Timing Metrics:', performanceMetrics.paintTimings);
  console.log('Largest Contentful Paint Metrics:', performanceMetrics.largestContentfulPaintTimings);

  await browser.close();
})();
