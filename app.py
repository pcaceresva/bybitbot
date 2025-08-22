from fastapi import FastAPI, Request
import os
import math
import requests
from pybit.unified_trading import HTTP

app = FastAPI()

# Variables de entorno
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Inicializamos sesión de Unified Demo
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True
)

# Configuración de trading
RISK_PERCENT = 0.10       # 10% del saldo
TP_PERCENT = 0.005        # 0.5%
SL_PERCENT = 0.005        # 0.5%
LEVERAGE = 10

@app.get("/demo-balance")
def get_demo_balance():
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED")
        return balance
    except Exception as e:
        return {"error": str(e)}

def get_symbol_info(symbol):
    """
    Obtiene minQty y precisión de cantidad del símbolo desde la API de Bybit
    """
    url = "https://api-testnet.bybit.com/v5/market/symbols"  # Demo Unified
    resp = requests.get(url)
    data = resp.json()
    info = next((s for s in data["result"]["list"] if s["name"] == symbol), None)
    if not info:
        return None, None
    min_qty = float(info["lotSizeFilter"]["minOrderQty"])
    qty_precision = int(info["lotSizeFilter"]["qtyPrecision"])
    return min_qty, qty_precision

def execute_trade(symbol: str, side: str):
    """
    Ejecuta un trade usando precio de mercado en Demo Unified, considerando minQty y precisión
    """
    try:
        # Obtenemos precio de mercado
        ticker = session.get_tickers(category="linear", symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición
        position_value = total_balance * RISK_PERCENT * LEVERAGE

        # Obtenemos minQty y precision
        min_qty, qty_precision = get_symbol_info(symbol)
        if min_qty is None:
            return {"error": f"Símbolo {symbol} no encontrado en API."}

        qty = max(round(position_value / price, qty_precision), min_qty)

        # Calculamos TP y SL
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        # Debug: imprimimos los valores antes de enviar
        print(f"Ejecutando trade → Symbol: {symbol}, Side: {side}, Qty: {qty}, TP: {tp_price}, SL: {sl_price}")

        # Ejecutamos la orden
        order = session.place_order(
            category="linear",       # Perpetuo USDT-M
            symbol=symbol,
            side=order_side,
            orderType="Market",
            qty=str(qty),
            leverage=LEVERAGE,
            takeProfit=str(round(tp_price, 6)),
            stopLoss=str(round(sl_price, 6))
        )
        return {"status": "success", "order": order}

    except Exception as e:
        return {"error": str(e)}

@app.post("/webhook")
async def webhook(request: Request):
    """
    Recibe alertas de TradingView en formato JSON:
    {
        "symbol": "BTCUSDT",
        "side": "LONG" or "SHORT"
    }
    """
    data = await request.json()
    symbol = data.get("symbol").replace(".P", "")
    side = data.get("side")

    if not symbol or not side:
        return {"error": "Faltan datos en la alerta"}

    return execute_trade(symbol, side)

@app.get("/test-order")
def test_order():
    """
    Orden de prueba rápida a precio de mercado
    """
    # Cambia el par a uno válido en tu Demo Unified
    symbol = "BTCUSDT"
    side = "LONG"  # o "SHORT"
    return execute_trade(symbol, side)

@app.get("/ping")
def ping():
    """
    Endpoint para mantener activo el servicio
    """
    return {"status": "ok"}
