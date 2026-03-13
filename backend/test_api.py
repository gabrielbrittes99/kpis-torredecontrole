from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.get("/api/torre/dashboard")
print(response.json())
