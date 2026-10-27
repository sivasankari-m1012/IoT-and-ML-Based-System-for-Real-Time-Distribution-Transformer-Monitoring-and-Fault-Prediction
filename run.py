"""Local dev entry point:  python run.py   (production uses gunicorn - see Dockerfile)."""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # HOST=0.0.0.0 lets the ESP32 on your Wi-Fi reach the server.
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
