import os
import time
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

BYBIT_URL = "https://api.bybit.com/v5/order/create"

def sign(params, secret):
    query = "&".join([f"{key}={value}" for key, value in sorted(params.items())])
    return hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()

def place_order(symbol, side, qty, order_type="Market"):
    timestamp = int(time.time() * 1000)
    params = {
        "apiKey": API_KEY,
        "symbol": symbol,
        "side": side,
        "orderType": order_type,
        "qty": str(qty),
        "timeInForce": "GoodTillCancel",
        "timestamp": str(timestamp),
        "recvWindow": "5000",
    }
    params["sign"] = sign(params, API_SECRET)
    r = requests.post(BYBIT_URL, data=params)
    return r.status_code, r.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_body = request.data.decode("utf-8").strip()
        print("Raw body:", raw_body)

        # intenta parsear JSON
        data = request.get_json(force=True, silent=True)
        print("JSON recibido:", data)

        symbol = "BTCUSDT.P"
        qty = 0.01

        if data:
            side = data.get("side", "Buy")
            symbol = data.get("symbol", symbol)
            qty = data.get("qty", qty)
        else:
            # si solo llega texto (ej: "long" o "short")
            if raw_body.lower() == "long":
                side = "Buy"
            elif raw_body.lower() == "short":
                side = "Sell"
            else:
                return jsonify({"error": f"Formato no reconocido: {raw_body}"}), 400

        status, response = place_order(symbol, side, qty)
        print("Bybit respuesta:", response)

        return jsonify({"status": status, "response": response})

    except Exception as e:
        print("Error en webhook:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Servidor de TradingView-Bybit funcionando 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
