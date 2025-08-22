from pybit.unified_trading import HTTP

# Inicializa la sesión en Demo Unified Trading
session = HTTP(
    demo=True,  # Demo
    api_key="kAEstgmtlzcLtBUC9D",
    api_secret="Qzn86OWLpLfLdHrGNOq8V6Vcli6oRiP0XJhG",
)

# Función para agregar fondos de prueba en Demo
def apply_demo_funds():
    response = session.post(
        path="/v5/account/demo-apply-money",
        json={
            "adjustType": 0,
            "utaDemoApplyMoney": [
                {"coin": "USDT", "amountStr": "109"},
                {"coin": "ETH", "amountStr": "1"}
            ]
        }
    )
    return response

# Función para ver balance de Unified Demo
def get_demo_balance():
    balance = session.get(
        path="/v5/account/wallet-balance",
        params={"accountType": "UNIFIED"}
    )
    return balance

# --- EJECUCIÓN ---
# Aplicar fondos de prueba
print("Aplicando fondos Demo...")
print(apply_demo_funds())

# Revisar saldo Demo
print("Balance Demo Unified:")
print(get_demo_balance())
