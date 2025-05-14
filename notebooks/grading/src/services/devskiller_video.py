import os
import asyncio
import datetime
from typing import Optional, List, Dict, Any

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class DevskillerVideoService:
    def __init__(self):
        self.base_url = "https://app.devskiller.com"
        self.auth_url = "https://auth.devskiller.com"
        self.username = os.getenv("DEVSKILLER_USERNAME")
        self.password = os.getenv("DEVSKILLER_PASSWORD")
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        
        if not PLAYWRIGHT_AVAILABLE:
            print("WARNING: Playwright not available. Install with 'pip install playwright'")
            print("Also install browser with 'python -m playwright install chromium'")

    async def _initialize_browser(self):
        """Initialize the browser if not already initialized"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not available. Install with 'pip install playwright'\n"
                "Also install browser with 'python -m playwright install chromium'"
            )
            
        if self._browser is None:
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=False)
                self._context = await self._browser.new_context()
                self._page = await self._context.new_page()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize browser: {str(e)}. Make sure you've installed the required packages.")
        
        return self._page
        
    async def authenticate(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Use Playwright to log in to DevSkiller and get authentication cookies.
        
        Args:
            username: DevSkiller username (email). Uses env if not provided.
            password: DevSkiller password. Uses env if not provided.
            
        Returns:
            The authentication cookies for API access.
        """
        username = username or self.username
        password = password or self.password
        
        try:
            page = await self._initialize_browser()
            
            # Go to auth login page
            print(f"Navigating to login page: {self.auth_url}/login")
            await page.goto(f"{self.auth_url}/login", wait_until="networkidle")
            
            # Take screenshot of initial page
            print("Initial login page screenshot removed")
            
            print("Entering email...")
            try:
                # Check for iframes
                frames = page.frames
                if len(frames) > 1:
                    print(f"Found {len(frames)} frames, switching to first iframe")
                    frame = frames[1]  # Use the first iframe if available
                else:
                    frame = page  # Use the main page

                # Try different strategies to find and fill the email field
                # Strategy 1: Use getByLabel
                try:
                    email_field = await frame.get_by_label("E-mail", exact=True).first.wait_for(timeout=5000)
                    await email_field.fill(username)
                    print("Found email field using getByLabel")
                except Exception as e1:
                    print(f"Could not find email field by label: {str(e1)}")
                    
                    # Strategy 2: Try with regular selector
                    try:
                        email_field = await frame.wait_for_selector('input[type="email"]', timeout=5000)
                        await email_field.fill(username)
                        print("Found email field using type=email selector")
                    except Exception as e2:
                        print(f"Could not find email field by type: {str(e2)}")
                        
                        # Strategy 3: Try with placeholder (case insensitive)
                        try:
                            email_field = await frame.wait_for_selector('input[placeholder="E-mail" i]', timeout=5000)
                            await email_field.fill(username)
                            print("Found email field using placeholder selector")
                        except Exception as e3:
                            print(f"Could not find email field by placeholder: {str(e3)}")
                            
                            # Strategy 4: Try using role
                            try:
                                await frame.get_by_role('textbox').first.fill(username)
                                print("Found email field using role selector")
                            except Exception as e4:
                                print(f"Could not find email field by role: {str(e4)}")
                                raise Exception("Could not find email field using any method")
                
                # Take a screenshot after filling email
                print("Email field filled, screenshot removed")
                
                # Try different strategies to click the Next button
                # Strategy 1: Use role
                try:
                    next_button = await frame.get_by_role('button', name="Next").first.wait_for(timeout=5000)
                    await next_button.click()
                    print("Clicked Next button using role selector")
                except Exception as e1:
                    print(f"Could not click Next button by role: {str(e1)}")
                    
                    # Strategy 2: Try with type
                    try:
                        next_button = await frame.wait_for_selector('button[type="submit"]', timeout=5000)
                        await next_button.click()
                        print("Clicked Next button using type selector")
                    except Exception as e2:
                        print(f"Could not click Next button by type: {str(e2)}")
                        
                        # Strategy 3: Try with text content
                        try:
                            next_button = await frame.wait_for_selector('button:has-text("Next")', timeout=5000)
                            await next_button.click()
                            print("Clicked Next button using text selector")
                        except Exception as e3:
                            print(f"Could not click Next button by text: {str(e3)}")
                            
                            # Strategy 4: Try any button
                            try:
                                buttons = await frame.query_selector_all('button')
                                if len(buttons) > 0:
                                    await buttons[0].click()
                                    print("Clicked first button found")
                            except Exception as e4:
                                print(f"Could not click any button: {str(e4)}")
                                raise Exception("Could not click Next button using any method")
                
                # Wait for password field to be visible
                await page.wait_for_load_state('networkidle')
                # await page.screenshot(path="after_next.png")  # screenshot disabled
                
            except Exception as e:
                print(f"Error with email entry: {str(e)}")
                # await page.screenshot(path="email_input_error.png")
                raise
            
            # Wait a moment for password field to appear
            await asyncio.sleep(2)
            
            print("Entering password...")
            try:
                # Check for iframes again (might have changed)
                frames = page.frames
                if len(frames) > 1:
                    print(f"Found {len(frames)} frames, switching to first iframe for password")
                    frame = frames[1]
                else:
                    frame = page

                # Try different strategies for password field
                # Strategy 1: Use getByLabel
                try:
                    password_field = await frame.get_by_label("Password", exact=True).first.wait_for(timeout=5000)
                    await password_field.fill(password)
                    print("Found password field using getByLabel")
                except Exception as e1:
                    print(f"Could not find password field by label: {str(e1)}")
                    
                    # Strategy 2: Try with regular selector
                    try:
                        password_field = await frame.wait_for_selector('input[type="password"]', timeout=5000)
                        await password_field.fill(password)
                        print("Found password field using type=password selector")
                    except Exception as e2:
                        print(f"Could not find password field by type: {str(e2)}")
                        
                        # Strategy 3: Try with placeholder
                        try:
                            password_field = await frame.wait_for_selector('input[placeholder="Password" i]', timeout=5000)
                            await password_field.fill(password)
                            print("Found password field using placeholder selector")
                        except Exception as e3:
                            print(f"Could not find password field by placeholder: {str(e3)}")
                            
                            # Strategy 4: Try using role
                            try:
                                textboxes = await frame.get_by_role('textbox').all()
                                if len(textboxes) > 1:
                                    await textboxes[1].fill(password)
                                    print("Found password field as second textbox")
                                else:
                                    print("Not enough textboxes found")
                                    raise Exception("Could not find password field")
                            except Exception as e4:
                                print(f"Could not find password field by role: {str(e4)}")
                                raise Exception("Could not find password field using any method")
                
                # Take a screenshot after filling password
                print("Password field filled, screenshot removed")
                
                # Try different strategies to click the Login button
                # Strategy 1: Use role
                try:
                    login_button = await frame.get_by_role('button', name="Log in").first.wait_for(timeout=5000)
                    await login_button.click()
                    print("Clicked Log in button using role selector")
                except Exception as e1:
                    print(f"Could not click Log in button by role: {str(e1)}")
                    
                    # Strategy 2: Try with type
                    try:
                        login_button = await frame.wait_for_selector('button[type="submit"]', timeout=5000)
                        await login_button.click()
                        print("Clicked Log in button using type selector")
                    except Exception as e2:
                        print(f"Could not click Log in button by type: {str(e2)}")
                        
                        # Strategy 3: Try with text content
                        try:
                            login_button = await frame.wait_for_selector('button:has-text("Log in")', timeout=5000)
                            await login_button.click()
                            print("Clicked Log in button using text selector")
                        except Exception as e3:
                            print(f"Could not click Log in button by text: {str(e3)}")
                            
                            # Strategy 4: Try any button
                            try:
                                buttons = await frame.query_selector_all('button')
                                if len(buttons) > 0:
                                    await buttons[0].click()
                                    print("Clicked first button found for login")
                            except Exception as e4:
                                print(f"Could not click any button for login: {str(e4)}")
                                raise Exception("Could not click Log in button using any method")

            except Exception as e:
                print(f"Error with password entry: {str(e)}")
                # await page.screenshot(path="password_input_error.png")
                raise
            
            # Wait for navigation
            await page.wait_for_load_state('networkidle')
            # await page.screenshot(path="after_login.png")
            
            # Check if we need to handle "no-access" page
            if "/no-access" in page.url:
                print("Detected 'no-access' page, clicking 'Go back to DevSkiller'")
                try:
                    # Try different strategies for the Go back button
                    # Strategy 1: Use role
                    try:
                        go_back_button = await page.get_by_role('button', name="Go back to DevSkiller").first.wait_for(timeout=5000)
                        await go_back_button.click()
                        print("Clicked Go back button using role selector")
                    except Exception as e1:
                        print(f"Could not click Go back button by role: {str(e1)}")
                        
                        # Strategy 2: Try with text content
                        try:
                            go_back_button = await page.wait_for_selector('button:has-text("Go back")', timeout=5000)
                            await go_back_button.click()
                            print("Clicked Go back button using text selector")
                        except Exception as e2:
                            print(f"Could not click Go back button by text: {str(e2)}")
                            
                            # Strategy 3: Try any button
                            try:
                                buttons = await page.query_selector_all('button')
                                if len(buttons) > 0:
                                    await buttons[0].click()
                                    print("Clicked first button found for go back")
                            except Exception as e3:
                                print(f"Could not click any button for go back: {str(e3)}")
                                # We'll continue anyway, might still have valid cookies
                    
                    await page.wait_for_load_state('networkidle')
                    # await page.screenshot(path="after_goback.png")
                except Exception as e:
                    print(f"Error handling no-access page: {str(e)}")
                    # await page.screenshot(path="no_access_error.png")
            
            # Get cookies from the browser
            cookies = await self._context.cookies()
            print(f"Got {len(cookies)} cookies")
            for i, cookie in enumerate(cookies):
                print(f"Cookie {i+1}: {cookie.get('name', 'unknown')} = {cookie.get('value', 'unknown')[:10]}...")
            
            # Take a screenshot of success
            print("Login process completed, screenshot removed")

            # ---------------------------------------------------------
            # NEW STEP: Navigate to the main DevSkiller application to
            # exchange SSO cookies so that we also obtain cookies scoped
            # for the `app.devskiller.com` domain (the domain where the
            # protected video lives).  Without this step we usually only
            # receive cookies for `auth.devskiller.com`, which results in
            # 401 responses when accessing resources under
            # `app.devskiller.com`.
            # ---------------------------------------------------------
            try:
                print(f"Navigating to DevSkiller app home page: {self.base_url}")
                await page.goto(self.base_url, wait_until="networkidle")
                await page.wait_for_load_state('networkidle')
                # await page.screenshot(path="after_app_home.png")
                print("Arrived at DevSkiller app, screenshot removed")
            except Exception as nav_err:
                # Not fatal—log and continue with whatever cookies we have
                print(f"Warning: could not navigate to DevSkiller app home: {str(nav_err)}")

            # Refresh cookies again **after** hitting the main app domain
            cookies = await self._context.cookies()
            print(f"Total cookies after visiting app: {len(cookies)}")
            for i, cookie in enumerate(cookies):
                print(f"Cookie {i+1}: {cookie.get('name', 'unknown')} (domain={cookie.get('domain','')}) = {cookie.get('value', '')[:10]}...")
            # ---------------------------------------------------------

            return cookies
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            # Take a screenshot to help diagnose issues
            # if self._page:
            #     await self._page.screenshot(path="auth_error.png")
            raise
        
    async def download_video(self, video_url: str, cookies=None, username: Optional[str] = None, 
                          password: Optional[str] = None, save_path: Optional[str] = None) -> bytes:
        """
        Download a video from DevSkiller using authentication cookies.
        
        Args:
            video_url: The direct URL to the video download.
            cookies: Authentication cookies from authenticate method. If not provided, will authenticate first.
            username: DevSkiller username (email). Uses env if not provided.
            password: DevSkiller password. Uses env if not provided.
            save_path: Optional path to save the video file.
            
        Returns:
            The video file as bytes.
        """
        try:
            await self._initialize_browser()
            
            if not cookies:
                cookies = await self.authenticate(username, password)
            
            # Set cookies for the browser context
            await self._context.clear_cookies()
            await self._context.add_cookies(cookies)
            
            # Create a single Cookie header from our cookies for manual request use
            cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            # Use Playwright's APIRequestContext to download the video avoiding browser navigation
            print(f"Initiating API request download for: {video_url}")
            api_request_context = self._context.request
            response = await api_request_context.get(video_url, headers={"Cookie": cookie_header})
            
            print(f"API response status: {response.status}")
            content_type = response.headers.get("content-type", "")
            print(f"API response content-type: {content_type}")
            
            # If unauthorized, attempt to re-authenticate once
            if response.status == 401:
                print("Received 401 from API request, refreshing authentication and retrying …")
                cookies = await self.authenticate(username, password)
                await self._context.clear_cookies()
                await self._context.add_cookies(cookies)
                cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                response = await api_request_context.get(video_url, headers={"Cookie": cookie_header})
                print(f"Retry API status: {response.status}")
                content_type = response.headers.get("content-type", "")
                print(f"Retry content-type: {content_type}")
            
            # Successful response – return bytes if it's a video/binary else raise
            if response.ok and ("application/octet-stream" in content_type or "video" in content_type):
                video_bytes = await response.body()
                if video_bytes:
                    if save_path is None:
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        os.makedirs("@videos", exist_ok=True)
                        save_path = os.path.join("@videos", f"video_{timestamp}.mp4")
                    with open(save_path, "wb") as f:
                        f.write(video_bytes)
                    print(f"Video saved to {save_path}")
                return video_bytes
            else:
                # As a fallback, attempt legacy browser navigation which may expose <video> tag
                print("Primary request download failed or returned non-video content, falling back to browser navigation …")
                try:
                    await self._page.goto(video_url)
                except Exception as nav_ex:
                    print(f"Browser navigation to video URL failed: {str(nav_ex)}")
            
            # Wait for any client-side redirects or processing
            await self._page.wait_for_load_state('networkidle')
            
            # If we couldn't get the video directly, it might be in a video element
            print("Looking for video elements...")
            video_elements = await self._page.query_selector_all('video')
            if video_elements and len(video_elements) > 0:
                print(f"Found {len(video_elements)} video elements")
                for video_element in video_elements:
                    src = await video_element.get_attribute('src')
                    if src:
                        print(f"Downloading video from src: {src}")
                        video_response = await self._page.goto(src)
                        if video_response:
                            video_bytes = await video_response.body()
                            
                            # Save video – create default path if not provided
                            if video_bytes:
                                if save_path is None:
                                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    os.makedirs("@videos", exist_ok=True)
                                    save_path = os.path.join("@videos", f"video_{timestamp}.mp4")
                                with open(save_path, "wb") as f:
                                    f.write(video_bytes)
                                print(f"Video saved to {save_path}")
                            
                            return video_bytes
            
            # Take a screenshot to help diagnose issues
            # await self._page.screenshot(path="video_download.png")
            # print("Saved page screenshot to video_download.png")
            
            # Get the content as a fallback
            html_content = await self._page.content()
            return html_content.encode('utf-8') if isinstance(html_content, str) else html_content
            
        except Exception as e:
            print(f"Download error: {str(e)}")
            # Take a screenshot to help diagnose issues
            # if self._page:
            #     await self._page.screenshot(path="download_error.png")
            raise
    
    async def close(self):
        """Close the browser instance"""
        if self._browser:
            try:
                await self._browser.close()
                await self._playwright.stop()
            except Exception as e:
                print(f"Error closing browser: {str(e)}")
            finally:
                self._browser = None
                self._context = None
                self._page = None
                self._playwright = None 