import json
import os
import asyncio
import time
from typing import Optional, Dict, Any
from playwright.async_api import Playwright, async_playwright, TimeoutError
from dotenv import load_dotenv
import redis

load_dotenv()

redis_client = redis.Redis.from_url(os.getenv("REDIS_CONN_STRING"))

class Devskiller:
    def __init__(self):
        self.base_url = "https://app.devskiller.com"
        self.auth_url = "https://auth.devskiller.com"
        self.username = os.getenv("DEVSKILLER_USERNAME") 
        self.password = os.getenv("DEVSKILLER_PASSWORD")
        # No external browser service required – Playwright will handle the browser locally
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
    
    async def init_browser(
        self,
        playwright: Playwright,
        headless: bool = True,
        storage_cookies: Optional[list[dict[str, Any]]] = None,
    ):
        """Launch a Chromium instance and prepare a new context & page.

        The browser is launched locally using Playwright, removing the need
        for the paid Browserbase service. The created browser, context and
        page are cached on the instance for further use and later teardown.
        """

        # Launch a fresh browser – use headless by default for server usage
        self._browser = await playwright.chromium.launch(headless=headless)

        # Create isolated context (cookies, storage, etc.) – if we already have a
        # cookie jar from Redis, preload it so every new page immediately sends
        # the right Cookie header on the first request.
        if storage_cookies:
            self._context = await self._browser.new_context(storage_state={"cookies": storage_cookies})
        else:
            self._context = await self._browser.new_context()

        # Open a new page/tab
        self._page = await self._context.new_page()

        return self._page
        
    async def update_cookies(self):
        async with async_playwright() as playwright:
            await self.init_browser(playwright, headless=False)

            if not self.username or not self.password:
                raise ValueError("DevSkiller credentials not provided.")
            
            username = self.username
            password = self.password
            
            try:
                # 1. Load login page
                await self._page.goto(f"{self.auth_url}/login", wait_until="domcontentloaded")

                # 2. Fill in the email address – try several common selectors to make the
                #    automation more resilient to minor UI changes.
                print("Filling in email address…")
                email_selector = "input#email, input[name='email'], input[type='email']"
                await self._page.locator(email_selector).first.fill(username)
                if await self._page.locator("input[type='password']").count() == 0:
                    # Try clicking the "Next" (or "Continue") button first
                    next_loc = self._page.locator("button:has-text('Next'), button:has-text('Continue'), button[type='submit']")
                    if await next_loc.count() > 0:
                        await next_loc.first.click()
                    else:
                        # As a fallback, press Enter in the e-mail field – many auth
                        # forms submit on Enter.
                        await self._page.locator(email_selector).first.press("Enter")

                    # Wait for password input to appear
                    await self._page.wait_for_selector("input[type='password']", timeout=15000)

                # 4. Fill in password and submit
                print("Filling password and logging in…")
                await self._page.get_by_role("button", name="Next").click()
                await self._page.wait_for_load_state("networkidle")
                await self._page.get_by_role("textbox", name="Password").fill(password)
                await self._page.get_by_role("button", name="Log in").click()
                
                # Wait longer for the authentication to complete
                await self._page.wait_for_load_state("networkidle", timeout=30000)
                
                # Give the authentication process some extra time to complete
                await asyncio.sleep(3)
                
                # Try to navigate to the base URL with retry mechanism
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        print(f"Navigating to {self.base_url} (attempt {attempt+1}/{max_retries})...")
                        # Use a longer timeout and different wait strategy
                        await self._page.goto(self.base_url, timeout=30000, wait_until="domcontentloaded")
                        # Wait for network to be idle after page load
                        await self._page.wait_for_load_state("networkidle", timeout=15000)
                        break
                    except Exception as e:
                        print(f"Navigation error: {str(e)}")
                        if attempt < max_retries - 1:
                            # Wait before retry
                            await asyncio.sleep(2)
                        else:
                            print("Max retries reached, continuing with current state")
                
                # Regular cookies
                cookies = await self._context.cookies()
                print(f"Retrieved {len(cookies)} cookies")
                # Persist cookies for later use (48 h TTL)
                redis_client.set("devskiller_cookies", json.dumps(cookies), ex=172800)
                return cookies
            finally:
                # Gracefully close resources
                await self._context.close()
                await self._browser.close()


    async def get_video_url(self, video_url: str):
        """Get video URL from Devskiller"""
        async with async_playwright() as playwright:
            try:
                # Get tokens from Redis
                redis_cookies = redis_client.get("devskiller_cookies")

                print(redis_cookies)
                
                if not redis_cookies:
                    print("No cookies found in Redis, refreshing session...")
                    await self.update_cookies()
                    redis_cookies = redis_client.get("devskiller_cookies")
                    if not redis_cookies:
                        raise ValueError("Failed to refresh cookies")
                
                redis_cookies = json.loads(redis_cookies)
                
                # Initialise browser *with the stored cookies pre-loaded* so the
                # very first navigation already carries the correct Cookie header.
                await self.init_browser(playwright, headless=False, storage_cookies=redis_cookies)

                # Navigate to target video page with retry mechanism
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        print(f"Navigating to {video_url} (attempt {attempt+1}/{max_retries})...")
                        await self._page.goto(video_url, timeout=30000, wait_until="domcontentloaded")
                        await self._page.wait_for_load_state("networkidle", timeout=15000)
                        break
                    except Exception as e:
                        print(f"Navigation error: {str(e)}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)
                        else:
                            raise ValueError(f"Failed to navigate to video URL after {max_retries} attempts")

                # Navigate to Section 2
                print("Clicking on Section 2...")
                await self._page.get_by_role("link", name="Section 2", exact=False).click()
                
                # Wait for download link and get it
                print("Waiting for download link...")
                await self._page.wait_for_selector("a:has-text('Download video')", timeout=15000)
                
                # Get download link
                download_link = await self._page.get_by_role("link", name="Download video").get_attribute("href")
                print(f"Download link: {download_link}")
                return download_link
            except Exception as e:
                print(f"Error in get_video_url: {str(e)}")
                # If we get an error that might be related to expired cookies, try refreshing them
                if "session" in str(e).lower() or "unauthorized" in str(e).lower() or "permission" in str(e).lower():
                    print("Session might be expired, attempting to refresh cookies...")
                    await self.update_cookies()
                    print("Cookies refreshed, please try your request again")
                raise
            finally:
                # Clean up
                if self._page:
                    await self._context.close()
                if self._browser:
                    await self._browser.close()

async def main():
    devskiller = Devskiller()
    # await devskiller.update_cookies()
    # Uncomment to test video URL retrieval
    # video_url = await devskiller.get_video_url("https://app.devskiller.com/candidates/fbd1b0af-25e1-4576-a078-c5c8b6659974/detail/invitations/11e98fec-dc81-4677-a9cc-5b8b7e9f816c")
    # print(f"Final video URL: {video_url}")

if __name__ == "__main__":
    asyncio.run(main())
