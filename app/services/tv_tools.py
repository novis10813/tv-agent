"""
LangChain TV control tools
"""

import time
import re
from typing import Literal
from urllib.parse import quote_plus

from langchain_core.tools import tool

from app.services.adb import adb_command, press_key, KEY_CODES, APPS


# ==================== TV Control Tools ====================
@tool
def tv_connect() -> str:
    """連接到 Android TV。在執行其他操作之前，請先確保已連接到電視。"""
    from app.config import settings
    result = adb_command(f"connect {settings.DEVICE_ID}", capture_output=True)
    if result and ("connected" in result.lower() or "already connected" in result.lower()):
        return f"✓ 已連接到 {settings.DEVICE_ID}"
    return f"✗ 無法連接到 {settings.DEVICE_ID}"


@tool
def tv_disconnect() -> str:
    """中斷與 Android TV 的連線"""
    from app.config import settings
    adb_command(f"disconnect {settings.DEVICE_ID}")
    return f"✓ 已中斷連線"


@tool
def tv_status() -> str:
    """取得電視連線狀態和裝置資訊"""
    from app.config import settings
    devices = adb_command("devices", capture_output=True) or ""
    if settings.DEVICE_ID not in devices:
        return f"✗ 未連接到 {settings.DEVICE_ID}"
    
    model = adb_command("shell getprop ro.product.model", capture_output=True) or "Unknown"
    android_version = adb_command("shell getprop ro.build.version.release", capture_output=True) or "Unknown"
    return f"✓ 已連接 | 型號: {model} | Android: {android_version}"


@tool
def tv_remote(key: Literal["home", "back", "up", "down", "left", "right", "ok", "enter", "menu", "search"]) -> str:
    """模擬遙控器按鍵。key: home=首頁, back=返回, up/down/left/right=方向, ok/enter=確認, menu=選單, search=搜尋"""
    keycode = KEY_CODES.get(key)
    if keycode:
        press_key(keycode)
        return f"✓ 已按下 {key}"
    return f"✗ 未知按鍵: {key}"


@tool
def tv_navigate(direction: Literal["up", "down", "left", "right"], steps: int = 1) -> str:
    """批次導航移動。direction: 方向, steps: 1-20 步"""
    steps = max(1, min(steps, 20))
    keycode = KEY_CODES.get(direction)
    for _ in range(steps):
        press_key(keycode)
        time.sleep(0.3)
    return f"✓ 向 {direction} 移動 {steps} 步"


@tool
def tv_volume(action: Literal["up", "down", "mute"], steps: int = 1) -> str:
    """調整音量。action: up=增加, down=降低, mute=靜音。steps: 1-15"""
    if action == "mute":
        press_key(KEY_CODES["volume_mute"])
        return "✓ 已切換靜音"
    
    steps = max(1, min(steps, 15))
    keycode = KEY_CODES.get(f"volume_{action}")
    for _ in range(steps):
        press_key(keycode)
        time.sleep(0.1)
    return f"✓ 音量{'增加' if action == 'up' else '降低'} {steps} 格"


@tool
def tv_power(action: Literal["on", "off", "toggle"]) -> str:
    """控制電源。action: on=開, off=關, toggle=切換"""
    key_map = {"on": "wakeup", "off": "sleep", "toggle": "power"}
    press_key(KEY_CODES[key_map[action]])
    return f"✓ 電源: {action}"


@tool
def tv_input_source(hdmi: Literal[1, 2, 3, 4]) -> str:
    """切換 HDMI 輸入源 (1-4)"""
    hw_port = hdmi + 4
    adb_command(
        f"shell am start -a android.intent.action.VIEW "
        f"-d 'content://android.media.tv/passthrough/com.mediatek.tvinput%2F.hdmi.HDMIInputService%2FHW{hw_port}' "
        f"-n org.droidtv.playtv/.PlayTvActivity -f 0x10000000"
    )
    return f"✓ 切換到 HDMI {hdmi}"


# ==================== Media Control ====================
@tool
def play_pause() -> str:
    """播放或暫停目前的影片"""
    press_key(KEY_CODES["play_pause"])
    return "✓ 已切換播放/暫停"


@tool
def rewind(app: Literal["youtube", "netflix"], seconds: int = 10) -> str:
    """倒退影片。app: youtube 或 netflix。seconds: 10-60 (10秒為單位)"""
    presses = max(1, min(seconds // 10, 6))
    key_code = KEY_CODES["rewind"] if app == "youtube" else KEY_CODES["left"]
    for _ in range(presses):
        press_key(key_code)
        time.sleep(0.2)
    time.sleep(0.3)
    press_key(KEY_CODES["ok"])
    return f"✓ {app} 倒退 {presses * 10} 秒"


@tool
def fast_forward(app: Literal["youtube", "netflix"], seconds: int = 10) -> str:
    """快轉影片。app: youtube 或 netflix。seconds: 10-60 (10秒為單位)"""
    presses = max(1, min(seconds // 10, 6))
    key_code = KEY_CODES["fast_forward"] if app == "youtube" else KEY_CODES["right"]
    for _ in range(presses):
        press_key(key_code)
        time.sleep(0.2)
    time.sleep(0.3)
    press_key(KEY_CODES["ok"])
    return f"✓ {app} 快轉 {presses * 10} 秒"


@tool
def stop_playback() -> str:
    """停止播放"""
    press_key(KEY_CODES["stop"])
    return "✓ 已停止"


# ==================== YouTube Tools ====================
@tool
def youtube_launch() -> str:
    """啟動 YouTube App"""
    app = APPS["youtube"]
    adb_command(f"shell am start -n {app['package']}/{app['activity']}")
    return "✓ 已啟動 YouTube"


@tool
def youtube_close() -> str:
    """關閉 YouTube App"""
    adb_command(f"shell am force-stop {APPS['youtube']['package']}")
    return "✓ 已關閉 YouTube"


@tool
def youtube_search(query: str) -> str:
    """在 YouTube 搜尋影片。query: 搜尋關鍵字"""
    encoded = quote_plus(query)
    adb_command(
        f"shell am start -a android.intent.action.VIEW "
        f"-d 'https://www.youtube.com/results?search_query={encoded}' {APPS['youtube']['package']}"
    )
    return f"✓ YouTube 搜尋: {query}"


@tool
def youtube_play(video_id: str) -> str:
    """播放指定 YouTube 影片。video_id: 影片 ID (如 dQw4w9WgXcQ)"""
    adb_command(
        f"shell am start -a android.intent.action.VIEW "
        f"-d 'https://www.youtube.com/watch?v={video_id}' {APPS['youtube']['package']}"
    )
    return f"✓ 播放影片: {video_id}"


@tool
def youtube_channel(channel: str) -> str:
    """開啟 YouTube 頻道。channel: 頻道 ID 或 @handle"""
    if channel.startswith("UC"):
        url = f"https://www.youtube.com/channel/{channel}"
    else:
        if not channel.startswith("@"):
            channel = f"@{channel}"
        url = f"https://www.youtube.com/{channel}"
    adb_command(f"shell am start -a android.intent.action.VIEW -d '{url}' {APPS['youtube']['package']}")
    return f"✓ 開啟頻道: {channel}"


@tool
def youtube_navigate(page: Literal["home", "subscriptions", "library"]) -> str:
    """前往 YouTube 頁面。page: home=首頁, subscriptions=訂閱, library=媒體庫"""
    url_map = {
        "home": "https://www.youtube.com",
        "subscriptions": "https://www.youtube.com/feed/subscriptions",
        "library": "https://www.youtube.com/feed/library"
    }
    adb_command(f"shell am start -a android.intent.action.VIEW -d '{url_map[page]}' {APPS['youtube']['package']}")
    return f"✓ YouTube {page}"


# ==================== Netflix Tools ====================
@tool
def netflix_launch() -> str:
    """啟動 Netflix App（不含自動選擇 profile）"""
    app = APPS["netflix"]
    adb_command(f"shell am start -n {app['package']}/{app['activity']}")
    return "✓ 已啟動 Netflix"


@tool
def netflix_close() -> str:
    """關閉 Netflix App"""
    adb_command(f"shell am force-stop {APPS['netflix']['package']}")
    return "✓ 已關閉 Netflix"


@tool
def netflix_search(query: str) -> str:
    """在 Netflix 搜尋。query: 搜尋關鍵字"""
    encoded = quote_plus(query)
    adb_command(
        f"shell am start -a android.intent.action.VIEW "
        f"-d 'https://www.netflix.com/search?q={encoded}' {APPS['netflix']['package']}"
    )
    return f"✓ Netflix 搜尋: {query}"


@tool
def netflix_play(title_id: str) -> str:
    """播放 Netflix 節目。title_id: 節目 ID"""
    adb_command(
        f"shell am start -a android.intent.action.VIEW "
        f"-d 'https://www.netflix.com/title/{title_id}' {APPS['netflix']['package']}"
    )
    return f"✓ 播放節目: {title_id}"


@tool
def netflix_navigate(page: Literal["home", "my_list"]) -> str:
    """前往 Netflix 頁面。page: home=首頁, my_list=我的片單"""
    url_map = {"home": "https://www.netflix.com/browse", "my_list": "https://www.netflix.com/browse/my-list"}
    adb_command(f"shell am start -a android.intent.action.VIEW -d '{url_map[page]}' {APPS['netflix']['package']}")
    return f"✓ Netflix {page}"


# ==================== Utility Tools ====================
@tool
def tv_screenshot(save_path: str = "/tmp/tv_screenshot.png") -> str:
    """截取電視畫面"""
    adb_command("shell screencap -p /sdcard/screenshot.png")
    adb_command(f"pull /sdcard/screenshot.png {save_path}")
    adb_command("shell rm /sdcard/screenshot.png")
    return f"✓ 截圖儲存至: {save_path}"


@tool
def tv_input_text(text: str) -> str:
    """在電視上輸入文字（僅支援英數）"""
    escaped = text.replace(" ", "%s")
    adb_command(f"shell input text '{escaped}'")
    return f"✓ 已輸入: {text}"


@tool
def tv_current_app() -> str:
    """取得目前執行的 App"""
    result = adb_command("shell dumpsys window | grep -E 'mCurrentFocus'", capture_output=True)
    if result:
        match = re.search(r'([a-zA-Z0-9_.]+)/[a-zA-Z0-9_.]+}', result)
        if match:
            package = match.group(1)
            names = {
                "com.google.android.youtube.tv": "YouTube",
                "com.netflix.ninja": "Netflix",
                "com.google.android.tvlauncher": "首頁"
            }
            return f"目前 App: {names.get(package, package)}"
    return "無法取得 App 資訊"


# ==================== All Tools ====================
# Note: tv_connect, tv_disconnect, tv_status 已移除，連線現在是自動的
ALL_TOOLS = [
    tv_remote, tv_navigate, tv_volume, tv_power, tv_input_source,
    play_pause, rewind, fast_forward, stop_playback,
    youtube_launch, youtube_close, youtube_search, youtube_play, youtube_channel, youtube_navigate,
    netflix_launch, netflix_close, netflix_search, netflix_play, netflix_navigate,
    tv_screenshot, tv_input_text, tv_current_app,
]
