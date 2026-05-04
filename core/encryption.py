"""
core/encryption.py – Symmetrische Verschlüsselung für gespeicherte Zugangsdaten.

Der FERNET_KEY muss in der .env-Datei stehen und geheim bleiben.
Beim ersten Start wird automatisch ein Schlüssel generiert.
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet


def _get_key() -> bytes:
    key = os.environ.get("FERNET_KEY")
    if key:
        return key.encode()

    # Beim ersten Start: Schlüssel generieren und in .env speichern
    new_key = Fernet.generate_key().decode()
    env_path = Path(__file__).parent.parent / ".env"
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"FERNET_KEY={new_key}\n")
    os.environ["FERNET_KEY"] = new_key
    print("FERNET_KEY generiert und in .env gespeichert – diese Datei nicht löschen!")
    return new_key.encode()


def encrypt(plaintext: str) -> str:
    return Fernet(_get_key()).encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return Fernet(_get_key()).decrypt(ciphertext.encode()).decode()
