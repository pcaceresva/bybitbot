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

def execute_trade(symbol: str, side: str):
    """
    Ejecuta un trade usando precio de mercado en Demo Unified,
    respetando los filtros de cantidad (lotSize) y precio (tickSize) del mercado.
    """
    try:
        # Obtenemos información del mercado para el par
        symbol_info = next(
            (s for s in session.get_symbols(category="linear")["result"]["list"] if s["name"] == symbol),
            None
        )
        if not symbol_info:
            return {"error": f"Símbolo {symbol} no encontrado en el mercado"}

        # Parámetros de lotSize y precio
        min_qty = float(symbol_info["lotSizeFilter"]["minQty"])
        qty_step = float(symbol_info["lotSizeFilter"]["qtyStep"])
        tick_size = float(symbol_info["priceFilter"]["tickSize"])

        # Obtenemos precio de mercado
        ticker = session.get_tickers(category="linear", symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición usando % de riesgo y apalancamiento
        position_value = total_balance * RISK_PERCENT * LEVERAGE
        raw_qty = position_value / price

        # Ajustamos qty según lotSize
        qty = max(round(raw_qty / qty_step) * qty_step, min_qty)
        qty = round(qty, 8)  # Para evitar decimales excesivos

        # Calculamos TP y SL según side
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:  # SHORT
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        # Ajustamos TP y SL según tickSize
        tp_price = round(tp_price / tick_size) * tick_size
        sl_price = round(sl_price / tick_size) * tick_size

        # Ejecutamos la orden a precio de mercado
        order = session.place_order(
            category="linear",
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
    symbol = "USELESSUSDT"
    side = "LONG"  # o "SHORT"
    return execute_trade(symbol, side)

@app.get("/ping")
def ping():
    return {"status": "alive"}





