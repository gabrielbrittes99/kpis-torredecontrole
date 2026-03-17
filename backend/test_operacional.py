import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    print("Testando endpoint /api/operacional/kpis?familia=todos...")
    resp = client.get("/api/operacional/kpis?familia=todos&ano=2026&mes=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Sucesso! Total Valor: {data.get('total_valor')}")
    
    print("\nTestando endpoint /api/operacional/custo-por-filial?familia=todos...")
    resp = client.get("/api/operacional/custo-por-filial?familia=todos&ano=2026&mes=3")
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        if data:
            print(f"Primeira filial: {data[0].get('filial')} | Eficiência: {data[0].get('eficiencia_index')}")
        else:
            print("Nenhuma filial retornada.")

except Exception as e:
    print(f"Erro no teste: {e}")
    import traceback
    traceback.print_exc()
