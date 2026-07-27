import serial
import requests
import time

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
FLASK_URL = "http://127.0.0.1:5000/api/sensors"

# Connect to Arduino
def connect_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            print(f"Connected to {SERIAL_PORT}")
            return ser
        except Exception as e:
            print(f"Serial connection failed: {e}")
            time.sleep(5)

ser = connect_serial()

while True:
    try:
        if ser.in_waiting > 0:

            line = ser.readline().decode("utf-8").strip()
            parts = line.split(",")

            # Expected format: N,P,K,pH,Temp,Hum
            if len(parts) == 6:
                try:
                    payload = {
                        "n": float(parts[0]),
                        "p": float(parts[1]),
                        "k": float(parts[2]),
                        "ph": float(parts[3]),
                        "temp": float(parts[4]),
                        "hum": float(parts[5])
                    }

                    # Send to Flask
                    response = requests.post(
                        FLASK_URL,
                        json=payload,
                        timeout=5
                    )

                    print(f"Sent → {payload}")
                    print(f"Server Response → {response.json()}")

                except ValueError:
                    print(f"Invalid sensor data: {line}")

            else:
                print(f"Incomplete data: {line}")

        time.sleep(1)

    except serial.SerialException:
        print("Serial disconnected. Reconnecting...")
        ser = connect_serial()

    except requests.exceptions.RequestException as e:
        print(f"Flask server not reachable: {e}")
        time.sleep(5)

    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(3)