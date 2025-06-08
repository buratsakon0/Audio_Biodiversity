import os
import asyncio
import websockets
import soundfile as sf
import numpy as np
from datetime import datetime

SAMPLE_RATE = 16000

client_buffers = {}
client_ids = {}

async def handle_client(websocket):
    client_ip = websocket.remote_address[0]
    client_id = client_ip  # เริ่มต้นใช้ IP เป็น ID แทน
    client_buffers[client_ip] = bytearray()

    print(f"🔌 Client connected: {client_ip}")

    try:
        async for message in websocket:
            if isinstance(message, str):
                if message.startswith("ID:"):
                    client_id = message[3:].strip()
                    client_ids[client_ip] = client_id
                    print(f"🆔 Client {client_ip} set ID: {client_id}")

                    # ย้าย buffer จาก IP ไปเป็น client_id
                    client_buffers[client_id] = client_buffers.pop(client_ip, bytearray())
                elif message == "END":
                    if client_id in client_buffers:
                        print(f"📁 Saving file from client {client_id}...")

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        folder = f"recordings/{client_id}"
                        os.makedirs(folder, exist_ok=True)

                        filename = f"{folder}/recording_{timestamp}.wav"
                        audio_array = np.frombuffer(client_buffers[client_id], dtype=np.int16)
                        sf.write(filename, audio_array, samplerate=SAMPLE_RATE, format="WAV")
                        print(f"✅ Saved: {filename}")

                        client_buffers[client_id] = bytearray()
                else:
                    print(f"ℹ️ Text message from {client_ip}: {message}")

            elif isinstance(message, bytes):
                if client_id in client_buffers:
                    client_buffers[client_id].extend(message)
                else:
                    client_buffers[client_id] = bytearray(message)

    except websockets.ConnectionClosed:
        print(f"❌ Client {client_ip} disconnected")
        if client_id in client_buffers:
            del client_buffers[client_id]
        if client_ip in client_ids:
            del client_ids[client_ip]

async def main():
    print("🎙️ Waiting for audio stream on ws://0.0.0.0:8765")
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
