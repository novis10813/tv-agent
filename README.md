# Agentic TV Controller

透過自然語言控制 Android TV - 整合版（不需要 MCP Server）

## 架構

```
iPhone Shortcuts → POST /command → LangChain + LiteLLM → ADB → 電視
```

## 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env
nano .env  # 填入 LITELLM_API_KEY
```

### 2. 啟動服務

```bash
uv run server.py
```

### 3. 測試

```bash
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "打開 YouTube"}'
```

## API

### POST /command
```json
{"text": "你的指令"}
```

### GET /health
健康檢查

### GET /tools
列出所有 tools

## 可用的 26 個 Tools

**連線**: tv_connect, tv_disconnect, tv_status

**遙控器**: tv_remote, tv_navigate, tv_volume, tv_power, tv_input_source

**媒體**: play_pause, rewind, fast_forward, stop_playback

**YouTube**: youtube_launch, youtube_close, youtube_search, youtube_play, youtube_channel, youtube_navigate

**Netflix**: netflix_launch, netflix_close, netflix_search, netflix_play, netflix_navigate

**工具**: tv_screenshot, tv_input_text, tv_current_app

## iPhone Shortcuts

1. 新增 Shortcut
2. 加入 "Get Contents of URL"
3. URL: `http://你的IP:8000/command`
4. Method: POST
5. Body: `{"text": "輸入指令"}`
