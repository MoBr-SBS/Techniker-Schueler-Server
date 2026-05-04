"""
app.py – Einstiegspunkt des Webservers.
Starte mit: python app.py
"""

from dotenv import load_dotenv
load_dotenv()

from core.server import create_app

if __name__ == "__main__":
    app = create_app()
    print("Server läuft auf http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=True)