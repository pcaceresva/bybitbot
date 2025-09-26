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
    print("Bybit status:", r.status_code)
    print("Bybit raw response:", r.text)
    return r.status_code, r.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_body = request.data.decode("utf-8").strip()
        print("=== NUEVA ALERTA RECIBIDA ===")
        print("Raw body recibido:", raw_body)

        # intenta parsear JSON
        data = request.get_json(force=True, silent=True)
        print("JSON recibido (puede ser None):", data)

        symbol = "BTCUSDT.P"
        qty = 0.01

        if data:
            side = data.get("side", "Buy")
            symbol = data.get("symbol", symbol)
            qty = data.get("qty", qty)
        else:
            # si solo llega texto plano
            if raw_body.lower() == "long":
                side = "Buy"
            elif raw_body.lower() == "short":
                side = "Sell"
            else:
                print("Formato no reconocido en alerta:", raw_body)
                return jsonify({"error": f"Formato no reconocido: {raw_body}"}), 400

        print(f"Enviando orden: {side} {qty} {symbol}")
        status, response = place_order(symbol, side, qty)
        print("Respuesta final de Bybit:", response)

        return jsonify({"
