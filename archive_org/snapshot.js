const puppeteer = require('puppeteer');
const winston = require('winston');

// Set up logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message }) => {
      return `${timestamp} - ${level}: ${message}`;
    })
  ),
  transports: [
    new winston.transports.File({ filename: 'monitor.log' })
  ]
});

// Function to log request and response
async function logRequestResponse(page, url) {
  const response = await page.goto(url, { waitUntil: 'networkidle2' });
  const status = response.status();
  const body = await page.content();
  
  logger.info(`Request URL: ${url}`);
  logger.info(`Response Status Code: ${status}`);
  logger.info(`Response Data (first 200 chars): ${body.slice(0, 200)}...`);
}

// Main function to scrape the page
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // URL to scrape
  const url = "https://web.archive.org/web/20240000000000*/engadget.com/entry/1234000017043956/";

  try {
    // Log the main page request and response
    await logRequestResponse(page, url);

    // Extract all links matching the specific format
    const targetLinks = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('a[href]'))
        .map(link => link.getAttribute('href'))
        .filter(href => href.includes('/engadget.com/entry/1234000027055663/'));
    });

    // For each target link, process and log request and response
    for (const targetLink of targetLinks) {
      const fullLink = `https://web.archive.org${targetLink}`;
      await logRequestResponse(page, fullLink);

      // Extract URLs within <p class="impatient"> from the target page
      const urls = await page.evaluate(() => {
        const impatientParagraph = document.querySelector('p.impatient');
        if (impatientParagraph) {
          return Array.from(impatientParagraph.querySelectorAll('a[href]'))
            .map(a => a.getAttribute('href'));
        }
        return [];
      });

      if (urls.length > 0) {
        console.log(`URL(s) found in ${fullLink}:`, urls);
      }
    }

  } catch (error) {
    logger.error(`Error processing URL ${url}: ${error.message}`);
  }

  await browser.close();
})();