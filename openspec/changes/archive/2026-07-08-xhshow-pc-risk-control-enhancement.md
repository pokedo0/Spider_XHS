# xhshow PC 风控增强归档

日期：2026-07-08

## 背景

Spider_XHS 原有 PC crawling 逻辑由 `XHS_Apis` 负责请求、分页和返回三元组，由 `spider_xhs.XhsPcClient` 提供稳定 facade。此次不把 `xhshow` 当完整爬虫替换，而是作为签名与风控增强层接入。

目标：

- 保持 `XhsPcClient`、`client.raw`、`XHS_Apis` 方法签名和返回格式不变。
- 使用 PyPI 依赖 `xhshow>=0.2.0`，便于后续 `pip install -U xhshow` 获取更新。
- 利用 `xhshow` 的 `x-s`、`x-s-common`、`x-rap-param`、trace id、search id、`xy-direction`、`SessionManager`。
- 保留旧 JS 签名作为 fallback，降低更新风险。

## 实现概览

新增内部模块：

- `xhs_utils/xhshow_adapter.py`

该模块作为深模块封装 `xhshow`，外部仍通过旧 helper 形状使用：

- `generate_request_params(cookies_str, api, data='', method='POST') -> (headers, cookies, body)`
- `generate_search_id(root_search_id=None)`
- `generate_search_request_id()`
- `generate_x_b3_traceid()`
- `generate_xray_traceid()`
- `generate_x_rap_param(api, data, app_id=None)`

`xhs_utils/xhs_util.py` 保留原函数名，内部优先调用 adapter；旧 JS 逻辑被改名为 `_legacy_*`，作为 fallback。

## 策略

签名模式：

- 默认 `SPIDER_XHS_SIGNER=auto`。
- `auto`：优先 `xhshow`，失败时 fallback 到旧 JS 签名。
- `xhshow`：强制使用 `xhshow`，失败直接抛错。
- `legacy`：强制使用旧 JS 签名。

endpoint 策略：

- `XYW_`：`feed`、`homefeed`、`search/notes`、`search/usersearch`、`user_posted`、`user/otherinfo`。
- `XYS_ + SessionManager`：普通 GET、评论、消息类接口等。
- `x-rap-param`：由 adapter 对 `feed`、`homefeed`、`search/notes`、`search/usersearch` 统一生成。

Session 策略：

- 每个 cookie 账户维护独立 `SessionManager`。
- session key 使用 `a1` 或 `web_session` 的 SHA-256 摘要前 12 位。
- 加锁保护 session 缓存。
- 日志不打印 cookie、token、完整签名。

## 关键改动

- `pyproject.toml` 新增依赖：`xhshow>=0.2.0`。
- `apis/xhs_pc_apis.py` 移除 PC endpoint 内手动重复设置 `x-rap-param`。
- `apis/xhs_pc_apis.py` 移除固定 `xy-direction = 13`，改用 `xhshow` 生成结果。
- 新增 `tests/test_xhshow_adapter.py` 覆盖 adapter 行为。

## 测试记录

已通过：

- `python -m unittest discover -s tests -p "test_xhshow_adapter.py"`：6/6 pass
- `python -m unittest discover -s tests -p "test_pc_facade.py"`：14/14 pass
- `python -m compileall -q spider_xhs tests xhs_utils apis`：pass
- `python -m pip install -e . --dry-run --no-deps`：pass
- signer smoke：`XYW_ True {"source_note_id":"n1"}`

全量测试现状：

- `python -m unittest discover -s tests -p "test_*.py"` 仍有 live API 相关失败。
- `test_pick_best_stream_from_real_api`：真实接口返回 `登录已过期`。
- `test_download_video_to_temp_dir`：真实接口返回成功但 `items` 为空，测试访问 `items[0]` 报 `IndexError`。

判断：

- adapter/facade/compile/package 相关检查通过。
- 全量失败来自真实 cookie 或真实接口数据状态，不是 adapter 单测回归。

## 后续建议

- 将真实网络测试与纯单元测试隔离，例如用环境变量显式启用 live tests。
- 为 `test_video_download.py` 增加 `items` 为空时的清晰失败信息，避免 `IndexError`。
- 后续若 `xhshow` 改变 `sign_headers_*` 接口，优先更新 adapter 和 `tests/test_xhshow_adapter.py`。
