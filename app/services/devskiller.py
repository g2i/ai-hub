import json
import os
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Playwright, async_playwright
from browserbase import Browserbase
from dotenv import load_dotenv
import redis

load_dotenv()

redis_client = redis.Redis.from_url(os.getenv("REDIS_CONN_STRING"))

bb = Browserbase(api_key=os.getenv("BROWSERBASE_API_KEY"))

class Devskiller:
    def __init__(self):
        self.base_url = "https://app.devskiller.com"
        self.auth_url = "https://auth.devskiller.com"
        self.username = os.getenv("DEVSKILLER_USERNAME") 
        self.password = os.getenv("DEVSKILLER_PASSWORD")
        self.api_key = os.getenv("BROWSERBASE_API_KEY")
        self.project_id = os.getenv("BROWSERBASE_PROJECT_ID")
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._session = None
    
    async def init_browser(self, playwright: Playwright):
        session = bb.sessions.create(project_id=os.getenv("BROWSERBASE_PROJECT_ID"))
        chromium = playwright.chromium
        browser = await chromium.connect_over_cdp(session.connect_url)
        
        # Assign browser and context to instance variables so they can be used across methods
        self._browser = browser
        self._context = browser.contexts[0]
        self._page = self._context.pages[0]
        self._session = session
        
        return self._page
        
    async def update_cookies(self):
        async with async_playwright() as playwright:
            await self.init_browser(playwright)

            if not self.username or not self.password:
                raise ValueError("DevSkiller credentials not provided.")
            
            username = self.username
            password = self.password
            
            try:
                await self._page.goto(f"{self.auth_url}/login", wait_until="networkidle")
                print("Filling email and submitting...")
                await self._page.fill("input#email", username)
                await self._page.click("button:has-text('Next')")
                
                # Wait for password field
                await self._page.wait_for_selector("input[type='password']", timeout=15000)
                
                # Fill password and login
                print("Filling password and logging in...")
                await self._page.fill("input[type='password']", password)
                await self._page.click("button:has-text('Log in')")
                
                # Wait for navigation to complete
                print("Waiting for navigation...")
                await self._page.wait_for_load_state("networkidle", timeout=30000)
                
                # Visit main app to get all cookies
                await self._page.goto(self.base_url, wait_until="networkidle")
                
                # Get all cookies
                cookies = await self._context.cookies()
                redis_client.set("devskiller_cookies", json.dumps(cookies), ex=172800)  # 48 hours TTL
                print(f"Authentication complete, collected {len(cookies)} cookies")
                return cookies
            finally:
                await self._page.close()
                await self._browser.close()
                print(f"Done! View replay at https://browserbase.com/sessions/{self._session.id}")


    async def get_video_url(self, video_url: str):
        """Get video URL from Devskiller"""
        async with async_playwright() as playwright:
            # Get tokens from Redis
            redis_cookies = redis_client.get("devskiller_cookies")
            if not redis_cookies:
                raise ValueError("No cookies found in Redis")
            redis_cookies = json.loads(redis_cookies)
            
            # Extract id_token and access_token from Redis cookies
            id_token = None
            access_token = None
            for cookie in redis_cookies:
                if cookie.get('name') == 'id_token':
                    id_token = cookie.get('value')
                elif cookie.get('name') == 'access_token':
                    access_token = cookie.get('value')
            
            if not id_token or not access_token:
                raise ValueError("id_token or access_token not found in Redis cookies")
            
            # Initialize browser
            await self.init_browser(playwright)
            
            # Define mock cookies with tokens from Redis
            cookies = [
                {"name": "id_token", "value": id_token, "domain": ".devskiller.com", "path": "/"},
                {"name": "access_token", "value": access_token, "domain": ".devskiller.com", "path": "/"}
            ]
            
            # Set cookies for authentication
            await self._context.add_cookies(cookies)
            
            # Go to video page
            print(f"Navigating to {video_url}...")
            await self._page.goto(video_url, wait_until="networkidle")
            
            try:
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
            finally:
                # Clean up
                await self._page.close()
                await self._browser.close()
                print(f"Done! View replay at https://browserbase.com/sessions/{self._session.id}")

async def main():
    async with async_playwright() as playwright:
        devskiller = Devskiller()
        # await devskiller.run(playwright)
        await devskiller.get_video_url("https://app.devskiller.com/candidates/fbd1b0af-25e1-4576-a078-c5c8b6659974/detail/invitations/11e98fec-dc81-4677-a9cc-5b8b7e9f816c")

if __name__ == "__main__":
    asyncio.run(main())
