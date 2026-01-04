"""
ADB helper functions for TV control
"""

import os
import subprocess
import time

from app.config import settings


KEY_CODES = {
    "home": 3, "back": 4, "up": 19, "down": 20, "left": 21, "right": 22,
    "ok": 23, "enter": 66, "menu": 82, "search": 84, "play_pause": 85,
    "stop": 86, "next": 87, "previous": 88, "rewind": 89, "fast_forward": 90,
    "volume_up": 24, "volume_down": 25, "volume_mute": 164,
    "power": 26, "sleep": 223, "wakeup": 224,
}

APPS = {
    "youtube": {
        "package": "com.google.android.youtube.tv",
        "activity": "com.google.android.apps.youtube.tv.activity.ShellActivity"
    },
    "netflix": {
        "package": "com.netflix.ninja",
        "activity": "com.netflix.ninja.MainActivity"
    }
}


def adb_command(cmd: str, capture_output: bool = False) -> str | None:
    """執行 ADB 指令"""
    full_cmd = f"adb -s {settings.DEVICE_ID} {cmd}"
    if capture_output:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    else:
        os.system(full_cmd)
        return None


def ensure_connection() -> bool:
    """確保 ADB 連線，如果未連線則自動連線"""
    devices = adb_command("devices", capture_output=True) or ""
    if settings.DEVICE_ID in devices:
        return True
    
    # 嘗試連線
    result = adb_command(f"connect {settings.DEVICE_ID}", capture_output=True)
    return result and ("connected" in result.lower() or "already connected" in result.lower())


def press_key(keycode: int) -> None:
    """按下指定按鍵"""
    adb_command(f"shell input keyevent {keycode}")


def enter_pin(pin: str) -> None:
    """輸入 PIN 碼"""
    for digit in pin:
        keycode = 7 + int(digit)
        press_key(keycode)
        time.sleep(0.2)


def select_netflix_profile(profile_index: int, pin: str | None = None) -> str:
    """選擇 Netflix profile 並輸入 PIN"""
    time.sleep(3)
    
    # 移動到正確的 profile (預設焦點在第一個)
    for _ in range(profile_index - 1):
        press_key(KEY_CODES["down"])
        time.sleep(0.3)
    
    # 選擇 profile
    press_key(KEY_CODES["ok"])
    
    # 如果有 PIN，等待 PIN 輸入畫面並輸入
    if pin:
        time.sleep(2)  # 等待 PIN 輸入畫面載入
        enter_pin(pin)
        # Netflix 會在輸入完 4 位數後自動確認，不需要按 OK
    
    time.sleep(2)  # 等待進入首頁
    return f"✓ 已選擇第 {profile_index} 個 profile"


def select_youtube_profile(profile_index: int) -> str:
    """
    選擇 YouTube 帳號
    
    YouTube TV 帳號切換流程：
    1. 載入完成後按 left 進入側邊欄
    2. 按 up 8 次確保在最上方
    3. 按 right 進入帳號區域（第一個帳號）
    4. 按 right 選擇第 N 個帳號
    """
    time.sleep(4)  # 等待 YouTube 完全載入
    
    # 進入側邊欄
    press_key(KEY_CODES["left"])
    time.sleep(0.3)
    
    # 按 up 8 次確保在最上方
    for _ in range(8):
        press_key(KEY_CODES["up"])
        time.sleep(0.2)
    
    # 按 right 進入帳號區域 (這時就是第一個帳號)
    press_key(KEY_CODES["right"])
    time.sleep(0.3)
    
    # 選擇第 N 個帳號 (profile_index=1 不需要再按 right)
    for _ in range(profile_index - 1):
        press_key(KEY_CODES["right"])
        time.sleep(0.3)
    
    # 確認選擇
    press_key(KEY_CODES["ok"])
    time.sleep(2)
    
    return f"✓ 已選擇第 {profile_index} 個 YouTube 帳號"
