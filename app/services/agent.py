"""
LangChain agent service
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.tv_tools import ALL_TOOLS


SYSTEM_PROMPT = """你是電視控制助手。根據用戶指令選擇合適的 tool 執行。

常見指令：
- "打開 YouTube" → youtube_launch
- "搜尋 XXX" → youtube_search 或 netflix_search
- "暫停" → play_pause
- "倒退10秒" → rewind(app="youtube" 或 "netflix", seconds=10)
- "快轉30秒" → fast_forward(app, seconds=30)
- "音量增加" → tv_volume(action="up")
- "回首頁" → tv_remote(key="home")

如果不確定目前是什麼 App，用 tv_current_app 查詢。
直接執行操作，不需要多餘解釋。"""


def create_agent():
    """Create LangChain agent with tools"""
    llm = ChatOpenAI(
        base_url=settings.LITELLM_BASE_URL,
        api_key=settings.LITELLM_API_KEY or "dummy",
        model=settings.LITELLM_MODEL,
    )
    return llm.bind_tools(ALL_TOOLS)


async def process_command(text: str, user_profile: dict | None = None) -> tuple[str, list[dict]]:
    """
    Process a natural language command
    
    Returns:
        tuple of (message, tool_results)
    """
    from app.services.adb import select_netflix_profile, select_youtube_profile, ensure_connection
    from app.services.tv_tools import netflix_launch, youtube_launch
    
    # 確保 ADB 連線
    ensure_connection()
    
    agent = create_agent()
    
    # Modify system prompt if user has profile
    system_content = SYSTEM_PROMPT
    if user_profile:
        system_content += f"\n\n用戶的設定: Netflix 第 {user_profile['netflix_profile_index']} 個, YouTube 第 {user_profile.get('youtube_profile_index', 1)} 個"
    
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=text)
    ]
    
    response = agent.invoke(messages)
    tool_results = []
    
    if response.tool_calls:
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            
            # Special handling for netflix_launch with user profile
            if tool_name == "netflix_launch" and user_profile:
                netflix_launch.invoke({})
                profile_result = select_netflix_profile(
                    user_profile["netflix_profile_index"],
                    user_profile.get("netflix_pin")
                )
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": f"✓ 已啟動 Netflix 並 {profile_result}"
                })
                continue
            
            # Special handling for youtube_launch with user profile
            if tool_name == "youtube_launch" and user_profile and user_profile.get("youtube_account_name"):
                from app.services.youtube_ocr import detect_and_find_youtube_account
                from app.services.adb import press_key, KEY_CODES
                import time
                
                # Launch YouTube first
                youtube_launch.invoke({})
                
                # Wait for account selection screen to load
                time.sleep(5)
                
                # Navigate to account selection area (left sidebar, then up to top)
                press_key(KEY_CODES["left"])
                time.sleep(0.5)
                for _ in range(8):
                    press_key(KEY_CODES["up"])
                    time.sleep(0.2)
                
                # Press right to enter account selection - this should show "誰在觀看" screen
                press_key(KEY_CODES["right"])
                time.sleep(2)  # Wait for account selection screen to fully load
                
                # NOW take screenshot and detect accounts
                target_name = user_profile["youtube_account_name"]
                position, detected = detect_and_find_youtube_account(target_name)
                
                if position:
                    # We're currently on the first account (after pressing right)
                    # Need to move right (position - 1) times to reach target
                    for _ in range(position - 1):
                        press_key(KEY_CODES["right"])
                        time.sleep(0.3)
                    press_key(KEY_CODES["ok"])
                    time.sleep(2)
                    result_msg = f"✓ 已啟動 YouTube 並選擇帳號 {target_name} (位置 {position}, 偵測到: {detected})"
                else:
                    # If not found, just press ok on current account
                    press_key(KEY_CODES["ok"])
                    result_msg = f"✗ 找不到帳號 {target_name}。偵測到: {detected}"
                
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result_msg
                })
                continue
            
            # Normal tool execution
            for t in ALL_TOOLS:
                if t.name == tool_name:
                    result = t.invoke(tool_args)
                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result
                    })
                    break
    
    if tool_results:
        message = " | ".join([r["result"] for r in tool_results])
    else:
        message = response.content or "沒有執行任何操作"
    
    return message, tool_results
