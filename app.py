from fastapi import FastAPI, Request
import os
from pybit.unified_trading import HTTP
import math

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

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    symbol = data.get("symbol")
    side = data.get("side")
    price = float(data.get("price"))

    if not symbol or not side or not price:
        return {"error": "Faltan datos en la alerta"}

    # Obtenemos saldo
    wallet = session.get_wallet_balance(accountType="UNIFIED")
    total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

    # Calculamos tamaño de la posición usando 10% del saldo
    position_value = total_balance * RISK_PERCENT * LEVERAGE

    # Obtenemos info de symbol para decimales
    symbol_info = session.get_symbol_info(symbol=symbol)
    qty_precision = symbol_info['result']['quantityPrecision']
    price_precision = symbol_info['result']['pricePrecision']

    # Calculamos cantidad y redondeamos según el precision
    qty = round(position_value / price, qty_precision)
    if qty <= 0:
        return {"error": "Cantidad calculada es menor o igual a 0"}

    # Calculamos TP y SL
    if side.upper() == "LONG":
        tp_price = round(price * (1 + TP_PERCENT), price_precision)
        sl_price = round(price * (1 - SL_PERCENT), price_precision)
    else:
        tp_price = round(price * (1 - TP_PERCENT), price_precision)
        sl_price = round(price * (1 + SL_PERCENT), price_precision)

    try:
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side="Buy" if side.upper() == "LONG" else "Sell",
            orderType="Market",
            qty=str(qty),
            leverage=LEVERAGE,
            takeProfit=str(tp_price),
            stopLoss=str(sl_price)
        )
        print("ORDER RESPONSE:", order)  # Para depuración
        return {"status": "success", "order": order}
    except Exception as e:
        print("ORDER ERROR:", str(e))
        return {"error": str(e)}


