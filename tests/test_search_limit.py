import os
from dotenv import load_dotenv
from apis.xhs_pc_apis import XHS_Apis

load_dotenv()
cookies = os.getenv("COOKIES")

api = XHS_Apis()

# print("========== 测试 page_size=20 ==========")
# success, msg, res = api.search_note("榴莲", cookies, page_size=20)
# if success:
#     items = res.get("data", {}).get("items", [])
#     print(f"请求成功！实际返回了 {items} 条数据。")
# else:
#     print(f"请求失败：{msg}")

print("\n========== 测试 page_size=5 ==========")
success, msg, res = api.search_note("榴莲", cookies)
if success:
    items = res.get("data", {}).get("items", [])
    print(f"请求成功！实际返回了 {items} 条数据。")
else:
    print(f"请求失败：{msg}")
