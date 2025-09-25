from flask import Flask, request, jsonify
import requests, time, hmac, hashlib, os

app = Flask(__name__)

# ===== CONFIGURACIÓN =====
API_KEY = os.getenv("BYBIT_API_KEY", "TU_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET", "TU_API_SECRET")
BASE_URL = "https://api.bybit.com"  # Demo o real usan el mismo endpoint

# ===== FUNCIONES =====
def sign_request(params: dict, secret: str):
    """Genera la firma para Bybit V5"""
    _val = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(bytes(secret, "utf-8"), bytes(_val, "utf-8"), hashlib.sha256).hexdigest()

def send_order(symbol: str, side: str, qty: float, order_type="Market"):
    """Envía una orden a Bybit"""
    endpoint = "/v5/order/create"
    url = BASE_URL + endpoint
    params = {
        "api_key": API_KEY,
        "timestamp": int(time.time() * 1000),
        "category": "linear",   # "linear" = USDT Perpetual, "spot" = spot
        "symbol": symbol,
        "side": side,           # "Buy" o "Sell"
        "orderType": order_type,
        "qty": str(qty)
    }
    params["sign"] = sign_request(params, API_SECRET)
    r = requests.post(url, data=params)
    return r.json()

# ===== ENDPOINT =====
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Payload recibido:", data)

        symbol = data.get("symbol")
        side = data.get("side")
        qty = data.get("qty", 0.01)  # valor por defecto si no viene en el JSON

        if not symbol or not side:
            return jsonify({"error": "Faltan parámetros (symbol, side)"}), 400

        result = send_order(symbol, side, qty)
        print("Respuesta Bybit:", result)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Bot de TradingView conectado a Bybit Demo ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
