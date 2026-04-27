# demo_iot.py - Simulates a smart meter sending data
import requests
import random
import time
from datetime import datetime

print("=" * 50)
print("IoT SMART METER SIMULATOR")
print("Demonstration for Water Supply Management System")
print("=" * 50)

meter_id = input("\nEnter meter ID (or press Enter for 'DEMO-001'): ").strip()
if not meter_id:
    meter_id = "DEMO-001"

print(f"\n📡 Simulating smart meter: {meter_id}")
print("🔄 Sending data to server every 10 seconds...")
print("📊 Watch the dashboard update in real-time!")
print("\nPress Ctrl+C to stop\n")

# API endpoint
url = "http://127.0.0.1:8000/api/meter-data/"

# Start with a baseline reading
reading = 1000.0

try:
    while True:
        # Simulate water usage (0.1 to 2.5 m³ per reading)
        usage = round(random.uniform(0.1, 2.5), 2)
        reading += usage
        
        # Send to server
        data = {"meter_id": meter_id, "reading": reading}
        response = requests.post(url, json=data)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('leak_detected'):
                print(f"[{timestamp}] ⚠️ LEAK DETECTED! Usage: {usage}m³ | Total: {reading:.2f}m³")
            else:
                print(f"[{timestamp}] ✅ Normal usage: +{usage}m³ | Total: {reading:.2f}m³")
        else:
            print(f"[{timestamp}] ❌ Error: {response.status_code}")
        
        time.sleep(10)  # Send every 10 seconds
        
except KeyboardInterrupt:
    print("\n\n🛑 Simulation stopped.")
    print("📊 Check the dashboard at: http://127.0.0.1:8000/dashboard/")