import asyncio
from playwright.async_api import async_playwright
import re

async def scrape_and_sum():
    seeds = range(9, 19)
    base_url = "https://sanand0.github.io/tdsdata/table_sum/seed_{}.html"
    total_sum = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for seed in seeds:
            url = base_url.format(seed)
            print(f"Scraping {url}...")
            await page.goto(url)
            
            # Find all numbers within <td> elements
            # We use a regex to extract digits even if there's whitespace/commas
            cells = await page.locator("td").all_inner_texts()
            for text in cells:
                # Extract numbers (handles decimals and integers)
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", text)
                for num in numbers:
                    total_sum += float(num)

        await browser.close()
        print("-" * 30)
        print(f"FINAL_TOTAL_SUM: {int(total_sum)}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(scrape_and_sum())
