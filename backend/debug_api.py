import sys
import traceback
try:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    print("Sending request...")
    response = client.get("/api/torre/dashboard")
    print("Status:", response.status_code)
    print("Body:", response.json())
except Exception as e:
    print("--- ERROR CAUGHT ---")
    with open("api_error.txt", "w") as f:
        traceback.print_exc(file=f)
    print("Check api_error.txt")
    sys.exit(1)
