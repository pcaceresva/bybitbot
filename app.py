from fastapi import FastAPI, Request
from pybit.unified_trading import HTTP

app = FastAPI()

# Inicializamos la sesión de Bybit Demo Unified Trading
session = HTTP(
    demo=True,                  # Demo (no testnet ni real)
    api_key="TU_API_KEY",
    api_secret="TU_API_SECRET",
)

# Función para obtener balance
def get_balance(category="spot"):
    try:
        balance = session.get_wallet_balance(category=category)
        return balance
    except Exception as e:
        return {"error": str(e)}

# Endpoint para probar balance
@app.get("/test-balance")
async def test_balance():
    balance = get_balance(category="spot")  # o "linear"
    return balance

# Endpoint de webhook para colocar orden (ejemplo)
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    # Ejemplo simple: colocar orden de compra BTCUSDT
    try:
        order = session.place_order(
            category="spot",          # o "linear"
            symbol="BTCUSDT",
            side="Buy",               # Buy o Sell
            orderType="Limit",        # Market o Limit
            qty="0.01",               # cantidad
            price="16000",            # precio límite
        )
        return {"status": "success", "order": order}
    except Exception as e:
        return {"status": "error", "message": str(e)}
