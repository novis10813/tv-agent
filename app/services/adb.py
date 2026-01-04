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

