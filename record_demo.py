import asyncio
import os
import shutil
from google.cloud import storage
from playwright.async_api import async_playwright

URL = "https://pavan-travel-guide-frontend-381379667098.us-central1.run.app"
BUCKET_NAME = "wanderlust-architect-media-qwiklabs-gcp-02-a7e255b6ed17"
OUTPUT_DIR = "/config/Desktop/Session1/wanderlust-architect/demo_recording"

async def record():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        print("Navigating to app...")
        await page.goto(URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 1. Primary capability: Search destinations
        prompt1 = "Search top travel destinations in Japan"
        print(f"Submitting Prompt 1: {prompt1}")
        await page.fill("#input", prompt1)
        await page.click("button[type='submit']")
        
        # Wait for agent response
        await page.wait_for_timeout(10000)

        # 2. Richer prompt: Weather lookup & artwork generation
        prompt2 = "What is the live weather in Paris, and generate destination artwork for a tropical beach sunset in Hawaii"
        print(f"Submitting Prompt 2: {prompt2}")
        await page.fill("#input", prompt2)
        await page.click("button[type='submit']")
        
        # Wait for agent tool response & generated artwork rendering
        await page.wait_for_timeout(15000)

        # Close page and context to flush video
        await page.close()
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
        print("Recorded video saved at:", video_path)

        # Copy to clean output location
        final_video = "/config/Desktop/Session1/wanderlust-architect/pavan_travel_guide_demo.webm"
        shutil.copy(video_path, final_video)
        print("Demo video created at:", final_video)

        # Upload to public Cloud Storage bucket
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob("demo/pavan_travel_guide_demo.webm")
        blob.upload_from_filename(final_video, content_type="video/webm")
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/demo/pavan_travel_guide_demo.webm"
        print("PUBLIC_DEMO_URL:", public_url)

if __name__ == "__main__":
    asyncio.run(record())
