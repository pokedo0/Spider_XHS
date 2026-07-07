import os
import json
from dotenv import load_dotenv
from spider_xhs import XhsPcClient

def main():
    load_dotenv()
    cookies = os.getenv("COOKIES")
    if not cookies:
        print("Please set COOKIES in .env file.")
        return

    client = XhsPcClient(cookies=cookies)
    
    url = "https://www.xiaohongshu.com/explore/6868e2d4000000001203e22b?xsec_token=AB8qYqeUS9p-YVmQe6M--RxdkxRh93RJRbklrmf-KiCdo=&xsec_source=pc_search&source=web_explore_feed"
    
    # 获取原始返回数据
    success, msg, data = client.raw.get_note_info(url, cookies, proxies=None) 
    
    if not success:
        print(f"Failed to fetch data: {msg}")
        return
        
    # 保存所有的原始数据到脚本所在目录的 raw_data.json
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print("已使用Spider_XHS的配置（含 Cookie）提取数据并保存至 raw_data.json。")
    print("-" * 50)
    
    # 打印视频可下载的所有源信息
    try:
        items = data.get("data", {}).get("items", [])
        if not items:
            print("未找到笔记项")
            return
            
        note = items[0].get("note_card", {})
        type_ = note.get("type")
        title = note.get("title", "")
        
        print(f"笔记标题: {title}")
        print(f"笔记类型: {type_}")
        
        if type_ == "video":
            video = note.get("video", {})
            media = video.get("media", {})
            stream = media.get("stream", {})
            
            print("\n发现以下可供下载的视频流 (直链/无水印):")
            for codec, streams in stream.items():
                if streams:
                    print(f"\n--- 编码: {codec.upper()} ({len(streams)} 个流) ---")
                    for i, s in enumerate(streams, 1):
                        quality = s.get('quality_type', '未知')
                        desc = s.get('stream_desc', '')
                        width = s.get('width', 0)
                        height = s.get('height', 0)
                        fps = s.get('fps', 0)
                        size_mb = s.get('size', 0) / (1024 * 1024)
                        url = s.get('master_url', '')
                        print(f"  源 {i}: [{quality}] {width}x{height} @{fps}fps")
                        print(f"    描述: {desc}")
                        print(f"    大小: {size_mb:.2f} MB")
                        print(f"    下载链接: {url}")
                        if s.get('backup_urls'):
                            print(f"    备用链接: {s['backup_urls'][0]}")
    except Exception as e:
        print(f"解析视频信息时出错: {e}")

if __name__ == "__main__":
    main()
