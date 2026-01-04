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
    from app.services.adb import select_netflix_profile
    from app.services.tv_tools import netflix_launch
    
    agent = create_agent()
    
    # Modify system prompt if user has profile
    system_content = SYSTEM_PROMPT
    if user_profile:
        system_content += f"\n\n用戶的 Netflix profile: 第 {user_profile['netflix_profile_index']} 個"
    
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
