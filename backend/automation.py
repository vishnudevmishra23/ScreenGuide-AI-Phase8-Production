from playwright.sync_api import sync_playwright


def search_youtube(query: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()
        page.goto("https://www.youtube.com", wait_until="domcontentloaded")

        page.locator("input#search").fill(query)
        page.locator("button#search-icon-legacy").click()

        page.wait_for_timeout(5000)

        return {
            "success": True,
            "message": f"YouTube search completed for: {query}"
        }