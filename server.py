"""
Agentic TV Controller
Webhook service that uses LiteLLM to control Android TV via MCP
"""

import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

from mcp_client import MCPClient

# Load environment variables
load_dotenv()

# Configuration
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm.homelab.com")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "llama-3.1-405b-instruct")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://192.168.0.13:8765/mcp")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Global clients
mcp_client: MCPClient | None = None
openai_client: AsyncOpenAI | None = None
openai_tools: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize clients on startup"""
    global mcp_client, openai_client, openai_tools
    
    print(f"🚀 Agentic TV Controller")
    print(f"   LiteLLM: {LITELLM_BASE_URL}")
    print(f"   Model: {LITELLM_MODEL}")
    print(f"   MCP Server: {MCP_SERVER_URL}")
    
    # Initialize MCP client
    mcp_client = MCPClient(MCP_SERVER_URL)
    
    try:
        # Initialize MCP session
        await mcp_client.initialize()
        print("   ✓ MCP connection established")
        
        # Get available tools
        mcp_tools = await mcp_client.list_tools()
        print(f"   ✓ {len(mcp_tools)} tools available")
        
        # Convert to OpenAI format
        openai_tools = mcp_client.mcp_tools_to_openai_tools(mcp_tools)
        
    except Exception as e:
        print(f"   ✗ MCP connection failed: {e}")
        print("   Server will start but TV control may not work")
    
    # Initialize OpenAI client (pointing to LiteLLM)
    openai_client = AsyncOpenAI(
        base_url=LITELLM_BASE_URL,
        api_key=LITELLM_API_KEY or "dummy-key"
    )
    
    yield
    
    print("Shutting down...")


app = FastAPI(
    title="Agentic TV Controller",
    description="Control your Android TV with natural language",
    lifespan=lifespan
)


class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    success: bool
    message: str
    tool_calls: list[dict] = []


SYSTEM_PROMPT = """你是一個電視控制助手。用戶會給你自然語言指令，你需要使用提供的 tools 來控制電視。

常見指令對應：
- "打開 YouTube" → youtube_launch
- "搜尋 XXX" → youtube_search 或 netflix_search
- "暫停" → play_pause
- "倒退 10 秒" → rewind(app, seconds)
- "快轉" → fast_forward(app, seconds)
- "音量調大/小" → tv_volume
- "回首頁" → tv_remote(key="home")
- "切換到 HDMI 1" → tv_input_source(hdmi=1)

注意：
- 使用 rewind/fast_forward 時，需要指定 app 是 "youtube" 還是 "netflix"
- 如果不確定當前是什麼 App，可以用 tv_current_app 查詢

請直接執行操作，不需要多餘的解釋。"""


@app.post("/command", response_model=CommandResponse)
async def handle_command(request: CommandRequest):
    """
    處理自然語言指令，透過 LLM 選擇並執行適當的 TV 控制操作
    """
    global mcp_client, openai_client, openai_tools
    
    if not mcp_client or not openai_client:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not openai_tools:
        # Try to refresh tools
        try:
            mcp_tools = await mcp_client.list_tools()
            openai_tools = mcp_client.mcp_tools_to_openai_tools(mcp_tools)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Cannot get tools: {e}")
    
    try:
        # Call LLM with tools
        response = await openai_client.chat.completions.create(
            model=LITELLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.text}
            ],
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        tool_results = []
        
        # Process tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute tool via MCP
                result = await mcp_client.call_tool(tool_name, tool_args)
                
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result
                })
        
        # Generate response message
        if tool_results:
            result_messages = [r["result"] for r in tool_results]
            final_message = " | ".join(result_messages)
        else:
            final_message = message.content or "沒有執行任何操作"
        
        return CommandResponse(
            success=True,
            message=final_message,
            tool_calls=tool_results
        )
        
    except Exception as e:
        return CommandResponse(
            success=False,
            message=f"Error: {str(e)}",
            tool_calls=[]
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "mcp_connected": mcp_client is not None,
        "tools_count": len(openai_tools)
    }


@app.get("/tools")
async def list_tools():
    """列出所有可用的 tools"""
    return {
        "tools": [t["function"]["name"] for t in openai_tools]
    }


def main():
    """Run the server"""
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
