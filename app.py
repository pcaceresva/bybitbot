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
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"raw": r.text}

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.data.decode("utf-8").strip()
    print("=== NUEVA ALERTA RECIBIDA ===")
    print("Raw body recibido:", raw_body)

    try:
        data = request.get_json(force=True, silent=True)
        print("JSON recibido (puede ser None):", data)
    except Exception as e:
        print("Error parseando JSON:", str(e))
        data = None

    symbol = "BTCUSDT.P"
    qty = 0.01
    side = "Buy"

    try:
        if data:
            side = data.get("side", "Buy")
            symbol = data.get("symbol", symbol)
            qty = data.get("qty", qty)
        else:
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

        return jsonify({"status": status, "response": response})

    except Exception as e:
        print("Error en webhook:", str(e))
        # aquí devolvemos el error explícito
        return f"Error en webhook: {str(e)}", 500

@app.route("/")
def home():
    return "Servidor de TradingView-Bybit funcionando 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
