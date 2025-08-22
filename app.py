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
LEVERAGE = 10

@app.get("/demo-balance")
def get_demo_balance():
    try:
        balance = session.get_wallet_balance(accountType="UNIFIED")
        return balance
    except Exception as e:
        return {"error": str(e)}

def calculate_qty(symbol: str, total_balance: float, leverage: int, risk_percent: float):
    """
    Calcula el qty para una orden de mercado considerando:
    - saldo disponible
    - riesgo
    - apalancamiento
    - restricciones del token (minOrderQty y qtyStep)
    """
    try:
        info = session.get_instruments_info(category="linear", symbol=symbol)
        data = info["result"]["list"][0]
        min_qty = float(data["minOrderQty"])
        qty_step = float(data["qtyStep"])
        last_price = float(data["lastPrice"])

        # Calculamos valor de posición
        position_value = total_balance * risk_percent * leverage
        raw_qty = position_value / last_price

        # Ajustamos qty a múltiplos de qty_step
        qty = math.floor(raw_qty / qty_step) * qty_step

        # Aseguramos que sea >= min_qty
        if qty < min_qty:
            qty = min_qty

        return qty, last_price

    except Exception as e:
        return None, None

def execute_trade(symbol: str, side: str):
    """
    Ejecuta un trade usando precio de mercado en Demo Unified.
    """
    try:
        # Obtenemos saldo
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        total_balance = float(wallet["result"]["list"][0]["totalAvailableBalance"])

        # Calculamos qty y precio de mercado
        qty, price = calculate_qty(symbol, total_balance, LEVERAGE, RISK_PERCENT)
        if qty is None:
            return {"error": "No se pudo calcular qty: token inválido o API"}

        order_side = "Buy" if side.upper() == "LONG" else "Sell"

        # Ejecutamos la orden
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side=order_side,
            orderType="Market",
            qty=str(qty),
            leverage=LEVERAGE
        )

        print(f"Ejecutando trade → Symbol: {symbol}, Side: {side}, Qty: {qty}, Precio mercado: {price}")
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
        symbol = data.get("symbol").replace(".P", "")
        side = data.get("side")

        if not symbol or not side:
            return {"error": "Faltan datos en la alerta"}

        return execute_trade(symbol, side)
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-order")
def test_order(symbol: str = "BTCUSDT", side: str = "LONG"):
    """
    Orden de prueba rápida a precio de mercado
    """
    return execute_trade(symbol, side)

@app.get("/ping")
def ping():
    """
    Endpoint para mantener vivo el servicio
    """
    return {"status": "ok"}
