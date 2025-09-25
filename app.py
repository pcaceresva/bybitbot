from flask import Flask, request, jsonify
import requests
import time
import hmac
import hashlib
import os

app = Flask(__name__)

# ===== CONFIGURACIÓN =====
API_KEY = os.getenv("BYBIT_API_KEY", "TU_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET", "TU_API_SECRET")
BASE_URL = "https://api.bybit.com"  # demo o real, funciona igual

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
        "category": "linear",   # "linear" = USDT Perpetual
        "symbol": symbol,
        "side": side,           # "Buy" o "Sell"
        "orderType": order_type,
        "qty": str(qty)
    }
    params["sign"] = sign_request(params, API_SECRET)
    r = requests.post(url, data=params)
print("Respuesta cruda de Bybit:", r.text)  # 👈 así vemos qué responde realmente Bybit
return {"raw": r.text}  # no intenta parsear a JSON


# ===== ENDPOINT =====
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Verifica que se reciba JSON
        if not request.is_json:
            return jsonify({"error": "No se recibió JSON"}), 400

        data = request.get_json()

        symbol = data.get("symbol")
        side = data.get("side")
        qty = data.get("qty", 0.01)

        # Validación mínima
        if not symbol or not side:
            return jsonify({"error": "Faltan parámetros (symbol o side)"}), 400

        # Envía la orden
        result = send_order(symbol, side, qty)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta principal para verificar que el servidor está arriba
@app.route("/", methods=["GET"])
def home():
    return "Bot de TradingView conectado a Bybit Demo ✅"

# ===== INICIO DE FLASK =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

