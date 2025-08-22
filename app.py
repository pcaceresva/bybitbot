from fastapi import FastAPI, Request
import uvicorn
from pybit.unified_trading import HTTP
import os

# 🔹 Configuración API Keys (usa tus credenciales reales en producción)
API_KEY = os.getenv("BYBIT_API_KEY", "tu_api_key")
API_SECRET = os.getenv("BYBIT_API_SECRET", "tu_api_secret")

# 🔹 Cliente Bybit (mainnet)
session = HTTP(
    testnet=False,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# FastAPI
app = FastAPI()

# 🔹 Configuración fija
TP_PERCENT = 0.5 / 100   # 0.5% TP
SL_PERCENT = 0.5 / 100   # 0.5% SL
RISK_USDT = 10           # Riesgo fijo en USDT por trade
LEVERAGE = 10            # Apalancamiento


# 🔹 Obtener precisión de cada símbolo
def get_symbol_info(symbol: str):
    try:
        resp = session.get_instruments_info(category="linear", symbol=symbol)
        if "result" in resp and "list" in resp["result"] and len(resp["result"]["list"]) > 0:
            info = resp["result"]["list"][0]
            price_scale = int(info["priceScale"])
            qty_step = float(info["lotSizeFilter"]["qtyStep"])
            min_qty = float(info["lotSizeFilter"]["minOrderQty"])
            return price_scale, qty_step, min_qty
    except Exception as e:
        print("❌ Error get_symbol_info:", e)
    return None, None, None


# 🔹 Calcular qty válido
def calculate_qty(symbol: str, risk_usdt: float):
    try:
        ticker = session.get_tickers(category="linear", symbol=symbol)
        if "result" not in ticker or "list" not in ticker["result"] or len(ticker["result"]["list"]) == 0:
            return None

        last_price = float(ticker["result"]["list"][0]["lastPrice"])
        price_scale, qty_step, min_qty = get_symbol_info(symbol)

        if not price_scale or not qty_step:
            return None

        # Qty base
        qty = risk_usdt / last_price

        # Ajustar a step permitido
        precision = len(str(qty_step).split(".")[1]) if "." in str(qty_step) else 0
        qty = round(qty - (qty % qty_step), precision)

        # Validar mínimo
        if qty < min_qty:
            qty = min_qty

        return qty, last_price
    except Exception as e:
        print("❌ Error calculate_qty:", e)
        return None


# 🔹 Endpoint para test de symbol
@app.get("/test-symbol")
def test_symbol(symbol: str = "BTCUSDT"):
    result = calculate_qty(symbol, RISK_USDT)
    if not result:
        return {"error": "No se pudo calcular qty"}
    qty, last_price = result
    return {
        "symbol": symbol,
        "lastPrice": last_price,
        "qty": qty
    }


# 🔹 Endpoint para enviar orden
@app.post("/trade")
async def trade(request: Request):
    try:
        data = await request.json()
        symbol = data.get("symbol", "BTCUSDT")
        side = data.get("side", "Buy")  # Buy / Sell

        qty_data = calculate_qty(symbol, RISK_USDT)
        if not qty_data:
            return {"error": "No se pudo calcular qty"}
        qty, last_price = qty_data

        # Calcular TP y SL
        if side == "Buy":
            tp = last_price * (1 + TP_PERCENT)
            sl = last_price * (1 - SL_PERCENT)
        else:  # Sell
            tp = last_price * (1 - TP_PERCENT)
            sl = last_price * (1 + SL_PERCENT)

        price_scale, qty_step, min_qty = get_symbol_info(symbol)
        tp = round(tp, price_scale)
        sl = round(sl, price_scale)

        order = session.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=str(qty),
            takeProfit=str(tp),
            stopLoss=str(sl),
            tpTriggerBy="LastPrice",
            slTriggerBy="LastPrice",
            timeInForce="GoodTillCancel"
        )
        return order

    except Exception as e:
        return {"error": f"No se pudo ejecutar trade: {e}"}


# 🔹 Iniciar servidor local
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
