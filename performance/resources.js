const puppeteer = require('puppeteer');
const fs = require('fs');
const { Parser } = require('json2csv');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();

  const url = 'https://www.engadget.com/best-wireless-earbuds-120058222.html?feature.getCommerceModulesFromRmp=1'; 
  await page.goto(url);

  const performanceMetrics = await page.evaluate(() => {
    const resourceTimings = performance.getEntriesByType('resource').map(resource => ({
      name: resource.name,
      startTime: resource.startTime,
      duration: resource.duration
    }));

    return {
      resourceTimings,
    };
  });

  // Flatten and combine all metrics into a single array for CSV export
  const combinedMetrics = [
    ...performanceMetrics.resourceTimings.map(r => ({ ...r, type: 'resource' })),
  ];

  // Convert JSON data to CSV
  const parser = new Parser();
  const csv = parser.parse(combinedMetrics);

  // Write CSV to a file
  //fs.writeFileSync('performance_metrics.csv', csv);

  console.log('Performance metrics saved to performance_metrics.csv');

  await browser.close();
})();
