import os
import time
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔑 Claves desde variables de entorno (Render → Dashboard → Environment)
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

# Endpoint base de Bybit (USDT Perpetual)
BYBIT_URL = "https://api.bybit.com/v5/order/create"

def sign(params, secret):
    """Genera la firma HMAC-SHA256 para Bybit"""
    query = "&".join([f"{key}={value}" for key, value in sorted(params.items())])
    return hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()

def place_order(symbol, side, qty, order_type="Market"):
    """Crea una orden en Bybit"""
    timestamp = int(time.time() * 1000)
    params = {
        "apiKey": API_KEY,
        "symbol": symbol,
        "side": side,  # Buy o Sell
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
    """Recibe alertas de TradingView"""
    try:
        data = request.json
        print("Alerta recibida:", data)

        symbol = data.get("symbol", "BTCUSDT")
        side = data.get("side", "Buy")
        qty = data.get("qty", 0.01)

        status, response = place_order(symbol, side, qty)

        return jsonify({"status": status, "response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Servidor de TradingView-Bybit funcionando 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
