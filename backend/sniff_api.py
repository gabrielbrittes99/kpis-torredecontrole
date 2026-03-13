import sys
import traceback
import json
from datetime import datetime
try:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    print("--- TESTING API ENDPOINT ---")
    response = client.get("/api/torre/dashboard")
    print(f"Status: {response.status_code}")
    data = response.json()
    if "error" in data.get("data", {}):
        print("!!! BACKEND LOGIC ERROR !!!")
        print(data["data"]["error"])
        print(data["data"].get("trace", ""))
    else:
        print("Success! Data looks good:")
        print(json.dumps(data, indent=2))
except Exception as e:
    print("--- CRITICAL SCRIPT ERROR ---")
    traceback.print_exc()
