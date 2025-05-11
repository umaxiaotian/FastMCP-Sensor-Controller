from fastmcp import FastMCP
import paho.mqtt.client as mqtt
from typing import Annotated
from pydantic import Field
import json
import threading

mcp = FastMCP("SensorController")

# MQTT設定
MQTT_BROKER = "mqtt"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/message"

# 最新のレスポンスを保持
latest_responses = {"dht11": None, "led": None}

# スレッドロック（複数リクエスト同時処理用）
response_locks = {"dht11": threading.Event(), "led": threading.Event()}


# MQTTハンドラ
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    """MQTT 受信ハンドラ 応答だけを扱う"""
    try:
        payload = json.loads(msg.payload.decode())
        cmd = payload.get("cmd")

        # ★ DHT11 の応答
        if (
            cmd == "dht11"
            and "temperature" in payload
            and "humidity" in payload
            and "status" in payload
        ):
            latest_responses["dht11"] = payload
            response_locks["dht11"].set()

        # ★ LED の応答
        elif cmd == "led" and "status" in payload:
            latest_responses["led"] = payload
            response_locks["led"].set()

    except Exception as e:
        print("MQTT message error:", e)


# MQTTクライアント起動
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.loop_start()


@mcp.tool()
def get_sensor_data():
    """
    DHT11センサーから温度と湿度を取得するエンドポイント。

    Returns:
        dict: {"temperature": float, "humidity": float}
    """
    cmd = {"cmd": "dht11", "value": "get"}
    latest_responses["dht11"] = None
    response_locks["dht11"].clear()

    mqtt_client.publish(MQTT_TOPIC, json.dumps(cmd))

    if response_locks["dht11"].wait(timeout=3):
        return latest_responses["dht11"]
    else:
        raise Exception("sensor did not respond")


@mcp.tool()
def set_led(
    r: Annotated[bool, Field(description="赤LEDを点灯するか")] = False,
    g: Annotated[bool, Field(description="緑LEDを点灯するか")] = False,
    b: Annotated[bool, Field(description="青LEDを点灯するか")] = False,
):
    """
    RGB LEDの点灯を制御するエンドポイント。

    Args:
        r (bool): 赤を点灯する場合 True
        g (bool): 緑を点灯する場合 True
        b (bool): 青を点灯する場合 True

    Returns:
        dict: 制御結果（例: {"status": "ok", "led": "rg"}）
    """
    color_cmd = ""
    if r:
        color_cmd += "r"
    if g:
        color_cmd += "g"
    if b:
        color_cmd += "b"
    command = {"cmd": "led", "value": color_cmd}
    latest_responses["led"] = None
    response_locks["led"].clear()

    mqtt_client.publish(MQTT_TOPIC, json.dumps(command))

    if response_locks["led"].wait(timeout=3):
        return latest_responses["led"]
    else:
        raise Exception("sensor did not respond")


if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8888,
        log_level="debug",
    )
