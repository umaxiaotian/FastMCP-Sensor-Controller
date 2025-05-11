"""MycroPythonのコード(ESP32用)"""
import network, time, machine, dht, ujson
from umqtt.simple import MQTTClient

# === 設定 =================================================
SSID     = "**********"      # <- WIFIのSSID
PASSWORD = "**********"      # <- WIFIのパスワード 
BROKER   = "***.***.***.***" # <- Dockerコンテナが立ち上がっているPCのローカルIP
TOPIC    = b"esp32/message"

# === ハードウェア ==========================================
sensor = dht.DHT11(machine.Pin(4))
LED = {c: machine.Pin(pin, machine.Pin.OUT)
       for c, pin in {"r": 13, "g": 12, "b": 14}.items()}

# === Wi‑Fi 接続 ===========================================
def wifi_connect():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(SSID, PASSWORD)
        while not sta.isconnected():
            time.sleep(0.5)
    return sta.ifconfig()[0]

# === LED 制御 =============================================
def set_led(colors: str) -> dict:
    for p in LED.values():
        p.off()
    for c in colors:
        LED.get(c) and LED[c].on()
    return {"cmd": "led", "led": colors or "off", "status": "ok"}

# === MQTT コールバック ====================================
def on_msg(topic, raw):
    try:
        req = ujson.loads(raw)
        if "status" in req:           # 応答は無視
            return

        if req.get("cmd") == "led":
            resp = set_led(req.get("value", ""))
        elif req == {"cmd": "dht11", "value": "get"}:
            sensor.measure()
            resp = {
                "cmd": "dht11",
                "temperature": sensor.temperature(),
                "humidity": sensor.humidity(),
                "status": "ok",
            }
        else:
            resp = {"cmd": "error", "msg": "unknown command"}

        client.publish(TOPIC, ujson.dumps(resp))

    except Exception as e:
        client.publish(TOPIC, ujson.dumps({"cmd": "error", "msg": str(e)}))

# === MQTT 接続（失敗しても戻らない） =======================
def mqtt_connect(retry_delay=2) -> MQTTClient:
    while True:
        try:
            c = MQTTClient("esp32", BROKER, keepalive=30)
            c.set_callback(on_msg)
            c.connect()
            c.subscribe(TOPIC)
            print("MQTT connected")
            return c
        except OSError as e:
            print("MQTT connect failed:", e, "– retry in", retry_delay, "s")
            time.sleep(retry_delay)

# === スタートアップ =======================================
print("IP:", wifi_connect())
client = mqtt_connect()
print("Listening on", TOPIC.decode())

# === メインループ =========================================
while True:
    try:
        client.check_msg()          # 受信処理（非ブロッキング）
    except OSError as e:
        # ソケットエラー：Wi‑Fi確認 → MQTT再接続
        print("MQTT error:", e, "– reconnecting…")
        time.sleep(1)
        print("IP:", wifi_connect())
        try:
            client.disconnect()
        except:
            pass
        client = mqtt_connect()
    time.sleep(0.1)
