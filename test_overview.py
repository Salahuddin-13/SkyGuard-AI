import urllib.request
import json

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/overview", timeout=30) as resp:
        data = json.loads(resp.read().decode())
        print("Total Stations:", data.get("total_stations"))
        print("Healthy Stations:", data.get("healthy"))
        print("Warning Stations:", data.get("warning"))
        print("Critical Stations:", data.get("critical"))
        print("Active Alerts:", len(data.get("alerts", [])))
        for k, st in list(data.get("stations", {}).items())[:5]:
            print(f"Station: {k} | Status: {st['status']} | T={st['temperature']}C | P={st['pressure']}hPa | RH={st['humidity']}%")
except Exception as e:
    print("Error:", e)
