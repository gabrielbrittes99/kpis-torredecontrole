from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
r = client.get("/api/torre/dashboard")
data = r.json().get("data", {})
situacao = data.get("situacao", {})
print("--- SITUACAO ---")
for k, v in situacao.items():
    print(f"{k}: {v}")

proj = data.get("projecao_detalhe", {})
print("--- PROJECAO ---")
for k, v in proj.items():
    print(f"{k}: {v}")
