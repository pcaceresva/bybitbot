from fastapi import FastAPI, Request
import os
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

# Decimales seguros para Demo Unified
DECIMALS_QTY = 3       # máximo 3 decimales en cantidad
DECIMALS_PRICE = 2     # máximo 2 decimales en precio
MIN_QTY = 0.001        # cantidad mínima por trade

@app.get("/demo-balance")
def get_demo_balance():
    """Devuelve saldo disponible en Demo Unified"""
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED")
        return balance
    except Exception as e:
        return {"error": str(e)}

def execute_trade(symbol: str, side: str):
    """
    Ejecuta un trade usando precio de mercado en Demo Unified.
    """
    try:
        # Obtenemos precio de mercado del símbolo
        ticker = session.get_tickers(category="linear", symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        # Obtenemos saldo disponible
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición
        raw_qty = total_balance * RISK_PERCENT * LEVERAGE / price
        qty = max(round(raw_qty, DECIMALS_QTY), MIN_QTY)

        # Calculamos TP y SL
        if side.upper() == "LONG":
            tp_price = round(price * (1 + TP_PERCENT), DECIMALS_PRICE)
            sl_price = round(price * (1 - SL_PERCENT), DECIMALS_PRICE)
            order_side = "Buy"
        else:  # SHORT
            tp_price = round(price * (1 - TP_PERCENT), DECIMALS_PRICE)
            sl_price = round(price * (1 + SL_PERCENT), DECIMALS_PRICE)
            order_side = "Sell"

        # Ejecutamos orden de mercado
        print(f"Symbol: {symbol}, Side: {side}, Qty: {qty}, TP: {tp_price}, SL: {sl_price}")

        order = session.place_order(
            category="linear",       # Perpetuo USDT-M
            symbol=symbol,
            side=order_side,
            orderType="Market",
            qty=str(qty),
            leverage=LEVERAGE,
            takeProfit=str(tp_price),
            stopLoss=str(sl_price)
        )
        return {"status": "success", "order": order}

    except Exception as e:
        return {"error": str(e)}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"error": "No se recibió JSON válido en el body"}

    symbol = data.get("symbol", "").replace(".P", "")
    side = data.get("side", "").upper()

    if not symbol or side not in ["LONG", "SHORT"]:
        return {"error": "Faltan datos o side inválido"}

    return execute_trade(symbol, side)

@app.get("/test-order")
def test_order():
    """
    Orden de prueba rápida a precio de mercado
    """
    symbol = "BTCUSDT"   # Cambia al símbolo de tu alerta
    side = "LONG"         # o "SHORT"
    return execute_trade(symbol, side)
    
@app.get("/ping")
def ping():
    """
    Endpoint para mantener vivo el webservice
    """
    return {"status": "OK"}


