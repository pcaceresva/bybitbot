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
    ajustando automáticamente cantidad mínima y decimales permitidos.
    """
    try:
        # Obtenemos información del símbolo (minQty y qtyPrecision)
        symbols_info = session.get_symbols(category="linear")
        info = next((s for s in symbols_info["result"]["list"] if s["name"] == symbol), None)
        if not info:
            return {"error": f"Símbolo {symbol} no encontrado en Bybit"}

        min_qty = float(info.get("lotSizeFilter", {}).get("minOrderQty", 0.001))
        qty_precision = int(info.get("lotSizeFilter", {}).get("qtyPrecision", 4))

        # Obtenemos precio de mercado
        ticker = session.get_tickers(category="linear", symbol=symbol)
        price = float(ticker["result"]["list"][0]["lastPrice"])

        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos tamaño de la posición
        position_value = total_balance * RISK_PERCENT * LEVERAGE
        qty = round(position_value / price, qty_precision)

        # Aseguramos que sea al menos la cantidad mínima
        if qty < min_qty:
            qty = min_qty

        # Calculamos TP y SL
        if side.upper() == "LONG":
            tp_price = price * (1 + TP_PERCENT)
            sl_price = price * (1 - SL_PERCENT)
            order_side = "Buy"
        else:
            tp_price = price * (1 - TP_PERCENT)
            sl_price = price * (1 + SL_PERCENT)
            order_side = "Sell"

        print(f"Ejecutando trade → Symbol: {symbol}, Side: {side}, Qty: {qty}, TP: {tp_price}, SL: {sl_price}")

        # Ejecutamos la orden
        order = session.place_order(
            category="linear",
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
    try:
        data = await request.json()
    except Exception as e:
        return {"error": f"JSON inválido: {str(e)}"}

    symbol = data.get("symbol")
    side = data.get("side")

    if not symbol or not side:
        return {"error": "Faltan datos en la alerta"}

    # Elimina el .P si tu ticker de TV lo incluye
    symbol = symbol.replace(".P", "")

    return execute_trade(symbol, side)

@app.get("/test-order")
def test_order():
    """
    Orden de prueba rápida a precio de mercado
    """
    symbol = "BTCUSDT"  # Cambia a un par válido en tu Demo Unified
    side = "LONG"        # o "SHORT"
    return execute_trade(symbol, side)

@app.get("/ping")
def ping():
    """
    Endpoint para mantener activo el webservice
    """
    return {"status": "alive"}

