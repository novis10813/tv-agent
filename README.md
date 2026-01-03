# Agentic TV Controller

透過自然語言控制 Android TV 的 webhook 服務。

## 架構

```
iPhone Shortcuts → Webhook (POST /command) → LiteLLM → MCP Client → Android TV
```

## 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env，填入你的 LITELLM_API_KEY
```

### 2. 啟動 Android TV MCP Server

```bash
cd /home/novis/docker/androidtv
uv run server.py
```

### 3. 啟動 Agentic Controller

```bash
cd /home/novis/docker/agentic_tv_controller
uv run server.py
```

## API

### POST /command

發送自然語言指令：

```bash
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "打開 YouTube"}'
```

回應：
```json
{
  "success": true,
  "message": "✓ 已啟動 YouTube",
  "tool_calls": [
    {"tool": "youtube_launch", "args": {}, "result": "✓ 已啟動 YouTube"}
  ]
}
```

### GET /health

健康檢查：
```bash
curl http://localhost:8000/health
```

### GET /tools

列出可用 tools：
```bash
curl http://localhost:8000/tools
```

## iPhone Shortcuts 設定

1. 打開 Shortcuts App
2. 新增 Shortcut
3. 加入 "Get Contents of URL" 動作
4. URL: `http://你的伺服器IP:8000/command`
5. Method: POST
6. Request Body: JSON `{"text": "你的指令"}`

## 環境變數

| 變數 | 說明 |
|------|------|
| `LITELLM_BASE_URL` | LiteLLM proxy URL |
| `LITELLM_API_KEY` | API Key |
| `LITELLM_MODEL` | 模型名稱 |
| `MCP_SERVER_URL` | Android TV MCP Server URL |
| `HOST` | 綁定地址 (預設 0.0.0.0) |
| `PORT` | 連接埠 (預設 8000) |
