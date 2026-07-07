import json
import os
from pathlib import Path
from dotenv import load_dotenv

from spider_xhs import XhsPcClient

def main():
    # Load cookies from .env
    env_path = Path(r"d:\Program\java_project\Spider_XHS\.env")
    load_dotenv(env_path)
    cookies = os.getenv("COOKIES")
    if not cookies:
        print("Error: COOKIES not found in .env")
        return

    client = XhsPcClient(cookies=cookies)
    
    # note_url = "https://www.xiaohongshu.com/explore/6a3e8dd10000000007024b6a?xsec_token=AB4YmCdYGXJth51GCFA2PPtFOZ98hST1jkgZ-WpipgMvQ=&xsec_source=pc_search&source=web_explore_feed"
    note_url = "https://www.xiaohongshu.com/explore/64300bec0000000007038034?xsec_token=ABqpipXC4rBHyhXnsZJoIqd9X351S2W9bFIv_3hRGCazM%3D&xsec_source=pc_search"
    
    print(f"Fetching note info for: {note_url}")
    # Get raw data
    success, msg, data = client.raw.get_note_info(note_url, cookies, None)
    
    if not success:
        print(f"Failed to fetch note: {msg}")
        return
        
    # Save raw json
    out_file = Path(r"d:\Program\java_project\Spider_XHS\tests\raw_note.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved raw JSON to {out_file}\n")
    
    try:
        note_card = data["data"]["items"][0]["note_card"]
        image_list = note_card.get("image_list", [])
        
        print("=== Image Information ===")
        print(f"Total images: {len(image_list)}")
        
        for i, img in enumerate(image_list):
            print(f"\n--- Image {i+1} ---")
            file_id = img.get("file_id")
            
            # Check Live photo
            live_photo = img.get("stream")
            if live_photo:
                print("Live Photo Stream detected!")
                h264_list = live_photo.get("h264", [])
                if h264_list:
                    print(f"  Live Video URL (master_url): {h264_list[0].get('master_url')}")
            else:
                print("Not a Live Photo.")
                
            # Print file ID (token)
            print(f"  File ID (Token): {file_id}")
            if file_id:
                no_watermark_url = f"https://sns-img-bd.xhscdn.com/{file_id}"
                print(f"  Generated No-Watermark URL (Auto): {no_watermark_url}")
                
                # Generate XHS-Downloader style formatted URLs
                print("  --- XHS-Downloader Style Format Testing ---")
                for fmt in ["png", "webp", "jpeg", "heic", "avif"]:
                    fmt_url = f"https://ci.xiaohongshu.com/{file_id}?imageView2/format/{fmt}"
                    print(f"    Format {fmt.upper():<4}: {fmt_url}")
                print("  -------------------------------------------")
                
            # Check info_list
            info_list = img.get("info_list", [])
            for j, info in enumerate(info_list):
                url = info.get("url")
                image_scene = info.get("image_scene")
                if url:
                    print(f"  [{j}] Scene '{image_scene}' URL (Usually Watermarked): {url}")
                    
    except Exception as e:
        print(f"Error parsing data: {e}")

if __name__ == "__main__":
    main()
