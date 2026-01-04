"""
YouTube account detection using OCR
"""

import subprocess
from PIL import Image
import pytesseract

from app.config import settings
from app.services.adb import adb_command


def capture_screen() -> str:
    """Capture TV screen and return local path"""
    path = "/tmp/tv_youtube_accounts.png"
    adb_command("shell screencap -p /sdcard/screenshot.png")
    adb_command(f"pull /sdcard/screenshot.png {path}")
    adb_command("shell rm /sdcard/screenshot.png")
    return path


def detect_youtube_accounts(image_path: str) -> list[dict]:
    """
    Detect YouTube account names and their positions.
    
    Returns:
        List of dicts with 'name' and 'x' position, sorted by x
    """
    img = Image.open(image_path)
    
    # Get OCR data with position info (use both Chinese and English)
    data = pytesseract.image_to_data(img, lang='chi_tra+eng', output_type=pytesseract.Output.DICT)
    
    accounts = []
    
    # Account names are around y=630-650 based on screenshot analysis
    # Filter out UI elements like "YouTube", "新增帳戶", "Kids", etc.
    skip_words = {
        'youtube', 'kids', '新增帳戶', '新', '增', '帳', '戶', '帳戶',
        '訪客', '身分', '觀看', '以', '@', '-q2m', '妹'
    }
    
    for i, text in enumerate(data['text']):
        text = text.strip()
        if not text:
            continue
        
        # Filter by confidence
        conf = int(data['conf'][i])
        if conf < 85:
            continue
        
        # Get position
        x = data['left'][i]
        y = data['top'][i]
        
        # Account names appear around y=630-660 range
        # x can be anywhere from 300 to 1200 (accounts area)
        if 620 < y < 660 and 200 < x < 1200:
            if text.lower() not in skip_words and len(text) > 1:
                accounts.append({
                    'name': text,
                    'x': x + data['width'][i] // 2,  # center x
                    'y': y
                })
    
    # Sort by x position (left to right)
    accounts.sort(key=lambda a: a['x'])
    
    return accounts


def find_account_position(target_name: str, accounts: list[dict]) -> int | None:
    """
    Find the position (1-indexed) of a target account name.
    
    Args:
        target_name: Name to find (case-insensitive partial match)
        accounts: List of detected accounts
    
    Returns:
        Position (1-indexed) or None if not found
    """
    target_lower = target_name.lower()
    
    for i, account in enumerate(accounts):
        if target_lower in account['name'].lower():
            return i + 1  # 1-indexed
    
    return None


def detect_and_find_youtube_account(target_name: str) -> tuple[int | None, list[str]]:
    """
    Capture screen, detect accounts, and find target account position.
    
    Args:
        target_name: Account name to find
    
    Returns:
        Tuple of (position or None, list of detected account names)
    """
    try:
        image_path = capture_screen()
        accounts = detect_youtube_accounts(image_path)
        
        account_names = [a['name'] for a in accounts]
        position = find_account_position(target_name, accounts)
        
        return position, account_names
    except Exception as e:
        print(f"YouTube account detection error: {e}")
        return None, []
