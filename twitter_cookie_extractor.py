# twitter_cookie_extractor.py
import os
import json
import asyncio
import redis
import logging
from playwright.async_api import async_playwright, TimeoutError
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Environment Variables ---
REDIS_URL = os.environ.get('REDIS_URL')

# CRITICAL SECURITY NOTE:
# Storing credentials in environment variables carries significant risk.
# If these credentials are ever compromised (e.g., due to a Render breach or misconfiguration),
# your Twitter account could be at serious risk.
# The most secure method for persistent authentication remains manually exporting cookies from your browser.
TWITTER_USERNAME = os.environ.get('TWITTER_USERNAME')
TWITTER_PASSWORD = os.environ.get('TWITTER_PASSWORD')

# --- Redis Client ---
redis_client = None

def get_redis_client():
    """Establishes and returns a Redis client connection."""
    global redis_client
    if redis_client is None:
        if not REDIS_URL:
            logger.critical("REDIS_URL environment variable is not set! Cannot connect to Redis.")
            return None
        try:
            redis_client = redis.from_url(REDIS_URL, decode_responses=False)
            redis_client.ping() # Test connection
            logger.info("Successfully connected to Upstash Redis.")
        except Exception as e:
            logger.critical(f"Redis connection failed: {e}")
            redis_client = None
        return redis_client

async def extract_twitter_cookies() -> str | None:
    """
    Automates login to X (Twitter) and extracts Netscape-formatted cookies.
    This is highly prone to breaking due to Twitter's anti-bot measures and UI changes.
    """
    if not TWITTER_USERNAME or not TWITTER_PASSWORD:
        logger.error("TWITTER_USERNAME or TWITTER_PASSWORD environment variables are not set. Cannot log in.")
        return None

    logger.info("Starting headless browser for Twitter cookie extraction...")
    async with async_playwright() as p:
        browser = None # Initialize browser to None outside try for finally block
        try:
            # Launch Chromium in headless mode for Render.
            # --no-sandbox is often required in Docker/containerized environments.
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context()
            page = await context.new_page()

            logger.info("Navigating to Twitter login page...")
            # Increased timeout to 60 seconds (60000ms) for initial navigation
            await page.goto("https://x.com/i/flow/login", wait_until='load', timeout=60000)

            # --- Twitter Login Flow (Highly Fragile & Subject to Change) ---
            # This part is the most likely to break. Selectors can change frequently.
            # Expect CAPTCHAs, phone/email verification steps, or other anti-bot challenges to halt automation.

            # Step 1: Enter Username/Email/Phone
            logger.info("Attempting to enter username...")
            # Wait for the input field to be visible and enabled
            await page.wait_for_selector('input[autocomplete="username"]', timeout=30000)
            # Use page.type with delay for more human-like typing
            await page.type('input[autocomplete="username"]', TWITTER_USERNAME, delay=100) # 100ms delay per character
            await page.keyboard.press('Enter') # Simulate pressing Enter

            # Step 2: Handle password input or potential verification prompts
            try:
                logger.info("Waiting for password field or verification prompt...")
                # Increased timeout for waiting for password field
                await page.wait_for_selector('input[name="password"]', timeout=30000)
                logger.info("Password field found. Entering password...")
                # Use page.type with delay for more human-like typing
                await page.type('input[name="password"]', TWITTER_PASSWORD, delay=100) # 100ms delay per character
                await page.keyboard.press('Enter')
            except TimeoutError:
                # If password field is not found, it might be a verification step or anti-bot block
                logger.warning("Password field not found directly. Checking for verification steps or other prompts.")
                # For robust debugging without logs, consider capturing screenshot/page content here
                # await page.screenshot(path="/tmp/timeout_screenshot_password_stage.png")
                # logger.error(f"Page content on password timeout: {await page.content()}")
                logger.error("Automated login failed: Likely stuck on a verification step (e.g., phone/email/username confirmation, CAPTCHA, or anti-bot block). Manual intervention required or selectors outdated.")
                return None # Indicate failure

            # Wait for successful login (e.g., redirect to home feed)
            logger.info("Waiting for post-login page...")
            # Increased timeout for post-login navigation to 90 seconds (90000ms)
            await page.wait_for_url("https://x.com/home", wait_until='load', timeout=90000)
            logger.info("Successfully logged into Twitter.")

            # --- Extract Cookies ---
            cookies = await context.cookies()
            netscape_cookies = ""
            # Netscape cookie file header format
            netscape_cookies += "# Netscape HTTP Cookie File\n"
            netscape_cookies += "# https://curl.haxx.se/docs/http-cookies.html\n"
            netscape_cookies += "# This file was generated by an automated service. Do not share.\n"
            
            for cookie in cookies:
                # Convert Playwright cookie dictionary to Netscape format string
                # Example Playwright cookie: {'name': 'auth_token', 'value': '...', 'domain': '.x.com', 'path': '/', 'expires': 1726772710.875, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'}
                include_subdomains = "TRUE" if cookie.get('domain', '').startswith('.') else "FALSE"
                expiry = int(cookie.get('expires', 0)) if cookie.get('expires') else 0
                secure = "TRUE" if cookie.get('secure') else "FALSE"
                
                netscape_cookies += (
                    f"{cookie.get('domain', '')}\t"
                    f"{include_subdomains}\t"
                    f"{cookie.get('path', '/')}\t"
                    f"{secure}\t"
                    f"{expiry}\t"
                    f"{cookie.get('name', '')}\t"
                    f"{cookie.get('value', '')}\n"
                )
            
            return netscape_cookies

        except TimeoutError as e:
            logger.error(f"Playwright operation timed out: {e}")
            # The screenshot saving to /tmp/ might work, but you can't access it directly from Render logs.
            # For local debugging, page.screenshot(path="timeout_screenshot.png") is useful.
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during cookie extraction: {e}", exc_info=True)
            return None
        finally:
            if browser: # Ensure browser is defined before trying to close
                await browser.close()
                logger.info("Browser closed.")

# --- FastAPI App ---
app = FastAPI()

@app.get("/")
async def health_check():
    """Simple health check endpoint for the service."""
    return JSONResponse(status_code=200, content={"status": "Twitter cookie extractor is running. Use /extract-twitter-cookies."})

@app.post("/extract-twitter-cookies")
async def trigger_twitter_cookie_extraction():
    """
    Triggers the automated extraction of Twitter cookies and stores them in Redis.
    """
    logger.info("Received request to extract Twitter cookies.")
    try:
        extracted_cookie_str = await extract_twitter_cookies()
        
        if extracted_cookie_str:
            r_client = get_redis_client()
            if not r_client:
                logger.error("Redis client not available for storing cookies.")
                raise HTTPException(status_code=500, detail="Redis connection failed.")
            
            redis_key = "twitter_cookies_netscape" # Key must match what your main bot uses
            r_client.set(redis_key, extracted_cookie_str.encode('utf-8'))
            logger.info(f"Successfully stored Twitter cookies in Redis under key: {redis_key}")
            return JSONResponse(status_code=200, content={"message": "Twitter cookies extracted and updated successfully!"})
        else:
            logger.error("Failed to extract Twitter cookies. Check logs for details.")
            raise HTTPException(status_code=500, detail="Failed to extract Twitter cookies.")

    except HTTPException as http_exc:
        raise http_exc # Re-raise FastAPI's HTTP exceptions
    except Exception as e:
        logger.error(f"Error in /extract-twitter-cookies endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
