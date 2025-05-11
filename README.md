# FastMCP Sensor Controller

このプロジェクトは、ESP32（MicroPython）と MQTT を介して連携し、MCP 経由でセンサーや LED を制御するための実験用サーバーです。
MQTTサーバーをAzure IoT Hubなどに置き換えると、インターネット越しにマイコンと会話させることもできます。

FastMCPのドキュメント: https://gofastmcp.com/getting-started/welcome
![esp32_circuit_ブレッドボード](https://github.com/user-attachments/assets/35f49110-3ae6-441f-9cb7-b3efbce09aa5)

## ✅ 構成

- ESP32（MicroPython）:
  - マイコン
    - ESP32-DevKit(※技適マーク付き)
      - https://amzn.to/4iWmr4s 
  - パーツ
    - DHT11 温湿度センサー　※DHT11 module
        - https://amzn.to/43jR2n8
    - RGB LED（GPIO 13, 12, 16） ※KY-016
        - https://amzn.to/4mbcnYp
  - 役割 
    - MQTT でコマンド受信・応答
- FastMCP:
  - SSE 経由で MQTT にコマンド送信
  - センサー取得・LED制御が可能


## 🚀 起動方法（MCPサーバー&MQTTブローカー）
```bash
docker compose up -d
```

## 💾 MicroPythonで書き込み
MicroPythonをESP32にインストールする方法は下記を参照ください。
https://zenn.dev/kotaproj/articles/d969fb39100da443f41f

esp32_micropythonフォルダ内のmain.pyをESP32にアップロードしてください。

（ThonnyなどのIDEを使うと便利です）


## 🧪 ClaudeDesktop (MCPクライアント)の設定
```json
{
  "mcpServers": {
    "sensorController": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:8888/sse"
      ]
    }
  }
}

```
