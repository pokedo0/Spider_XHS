import os
from dotenv import load_dotenv
from apis.xhs_pc_apis import XHS_Apis

def main() -> None:
    load_dotenv()
    cookies = os.getenv("COOKIES")
    if not cookies:
        raise RuntimeError("COOKIES is required for this live scratch test")

    with XHS_Apis() as api:
        print("\n========== 测试 page_size=5 ==========")
        success, msg, res = api.search_note("榴莲", cookies)
        if success:
            items = res.get("data", {}).get("items", [])
            print(f"请求成功！实际返回了 {items} 条数据。")
        else:
            print(f"请求失败：{msg}")


if __name__ == "__main__":
    main()
