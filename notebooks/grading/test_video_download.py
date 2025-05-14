#!/usr/bin/env python
import asyncio
import os
from src.services.devskiller_video import DevskillerVideoService

async def main():
    """Test the DevskillerVideoService by downloading a video."""
    video_url = "https://app.devskiller.com/rest/admin/candidates/fbd1b0af-25e1-4576-a078-c5c8b6659974/invitations/11e98fec-dc81-4677-a9cc-5b8b7e9f816c/answerSheet/S1F/answers/2105736/video-capture/download"
    save_path = "downloaded_video.mp4"
    
    print("Initializing DevskillerVideoService...")
    service = DevskillerVideoService()
    
    try:
        print("Authenticating...")
        cookies = await service.authenticate(
            username=os.getenv("DEVSKILLER_USERNAME"),
            password=os.getenv("DEVSKILLER_PASSWORD")
        )
        
        if cookies:
            print(f"Authentication successful! Got {len(cookies)} cookies.")
        
        print(f"Downloading video from {video_url}...")
        video_bytes = await service.download_video(
            video_url=video_url,
            cookies=cookies, 
            save_path=save_path
        )
        
        if video_bytes:
            print(f"Download successful! Got {len(video_bytes)} bytes.")
            print(f"Saved to {save_path}")
        else:
            print("Download failed - no bytes returned.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        print("Closing browser...")
        await service.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main()) 