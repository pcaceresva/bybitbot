from fastapi import FastAPI, Request
from pybit.unified_trading import HTTP
from decimal import Decimal
import os

app = FastAPI()

# Credenciales desde variables de entorno
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

# Cliente Bybit Demo (cámbialo a live si usas producción)
session = HTTP(
    testnet=True,
    api_key=API_KEY,
    api_secret=API_SECRET
)

# Porcentaje fijo de TP y SL
TP_PERCENT = 0.5 / 100   # 0.5%
SL_PERCENT = 0.5 / 100   # 0.5%

# --- Función para ajustar qty al paso permitido por Bybit ---
def ajustar_qty(qty, step):
    step = Decimal(str(step))
    qty = Decimal(str(qty))
    return float((qty // step) * step)  # redondea hacia abajo

# --- Endpoint de prueba ---
@app.get("/")
async def root():
    return {"status": "BybitBot API funcionando"}

# --- Endpoint para ejecutar trade ---
@app.post("/trade")
async def trade(request: Request):
    try:
        data = await request.json()
        symbol = data.get("symbol")
        side = data.get("side")
        leverage = data.get("leverage", 10)
        usdt_amount = data.get("usdt", 10)  # monto en USDT

        if not symbol or not side:
            return {"error": "Faltan parámetros (symbol, side)"}

        # --- Obtener info del símbolo ---
        info = session.get_instruments_info(category="linear", symbol=symbol)
        if "result" not in info or not info["result"]["list"]:
            return {"error": f"No se encontró info del símbolo {symbol}"}

        token_info = info["result"]["list"][0]
        price = float(token_info["lastPrice"])
        qty_step = float(token_info["lotSizeFilter"]["qtyStep"])
        min_qty = float(token_info["lotSizeFilter"]["minOrderQty"])

        # --- Calcular qty en base a USDT asignado ---
        raw_qty = usdt_amount / price
        qty = ajustar_qty(raw_qty, qty_step)

        if qty < min_qty:
            return {"error": f"Cantidad {qty} menor al mínimo permitido {min_qty}"}

        # --- Calcular TP y SL ---
        if side.lower() == "buy":
            tp = price * (1 + TP_PERCENT)
            sl = price * (1 - SL_PERCENT)
        else:
            tp = price * (1 - TP_PERCENT)
            sl = price * (1 + SL_PERCENT)

        # --- Crear orden a mercado ---
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side=side.capitalize(),
            orderType="Market",
            qty=str(qty),
            leverage=str(leverage),
            takeProfit=str(round(tp, 2)),
            stopLoss=str(round(sl, 2))
        )

        return {"status": "Orden enviada", "order": order, "qty": qty, "price": price}

    except Exception as e:
        return {"error": f"No se pudo ejecutar trade: {str(e)}"}
