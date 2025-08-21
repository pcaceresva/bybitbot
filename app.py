from fastapi import FastAPI, Request
import requests, hmac, hashlib, time, os

app = FastAPI()

# Usa variables de entorno en Render para mayor seguridad
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BASE_URL = "https://api-testnet.bybit.com"  # ⚠️ Usa testnet primero

def sign(params, secret):
    qs = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    symbol = data["symbol"]
    side = data["side"]
    qty = data["qty"]
    leverage = data.get("leverage", 10)
    tp_percent = data.get("tp_percent", 1.0)
    sl_percent = data.get("sl_percent", 0.5)

    # Precio actual
    r = requests.get(BASE_URL + "/v2/public/tickers", params={"symbol": symbol})
    last_price = float(r.json()["result"][0]["last_price"])

    # Calcula TP y SL
    if side == "Buy":
        tp_price = last_price * (1 + tp_percent/100)
        sl_price = last_price * (1 - sl_percent/100)
    else:
        tp_price = last_price * (1 - tp_percent/100)
        sl_price = last_price * (1 + sl_percent/100)

    # Orden de entrada
    order = {
        "api_key": API_KEY,
        "symbol": symbol,
        "side": side,
        "order_type": "Market",
        "qty": qty,
        "time_in_force": "GoodTillCancel",
        "reduce_only": False,
        "close_on_trigger": False,
        "timestamp": int(time.time() * 1000)
    }
    order["sign"] = sign(order, API_SECRET)
    entry_res = requests.post(BASE_URL + "/v2/private/order/create", data=order)

    # Orden TP
    tp = {
        "api_key": API_KEY,
        "symbol": symbol,
        "side": "Sell" if side == "Buy" else "Buy",
        "order_type": "Limit",
        "qty": qty,
        "price": round(tp_price, 2),
        "time_in_force": "GoodTillCancel",
        "reduce_only": True,
        "timestamp": int(time.time() * 1000)
    }
    tp["sign"] = sign(tp, API_SECRET)
    tp_res = requests.post(BASE_URL + "/v2/private/order/create", data=tp)

    # Orden SL
    sl = {
        "api_key": API_KEY,
        "symbol": symbol,
        "side": "Sell" if side == "Buy" else "Buy",
        "order_type": "StopMarket",
        "qty": qty,
        "stop_px": round(sl_price, 2),
        "base_price": round(last_price, 2),
        "time_in_force": "GoodTillCancel",
        "reduce_only": True,
        "timestamp": int(time.time() * 1000)
    }
    sl["sign"] = sign(sl, API_SECRET)
    sl_res = requests.post(BASE_URL + "/v2/private/stop-order/create", data=sl)

    return {
        "entry": entry_res.json(),
        "tp": tp_res.json(),
        "sl": sl_res.json()
    }
