"""
core/encryption.py – Verschlüsselung für gespeicherte Zugangsdaten.

Neue Credentials werden mit einem nutzereigenen Key verschlüsselt, der
beim Login aus dem Passwort abgeleitet wird (PBKDF2-HMAC-SHA256 + Fernet).
Dadurch reicht die Datenbank allein nicht aus – ohne das Login-Passwort
des Nutzers können gespeicherte WebUntis-Credentials nicht entschlüsselt werden.

Alte Credentials (FERNET_KEY aus .env) werden beim ersten Login automatisch migriert.
"""

import base64
import hashlib
import os
from pathlib import Path

from cryptography.fernet import Fernet


# ── Nutzerspezifischer Key (neue Methode) ─────────────────────────────────────

def derive_key(password: str, salt: bytes) -> bytes:
    """Leitet einen Fernet-Key aus Login-Passwort + Salt ab (PBKDF2-HMAC-SHA256, 300 000 Iterationen)."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 300_000, dklen=32)
    return base64.urlsafe_b64encode(dk)


def encrypt_with_key(plaintext: str, key: bytes) -> str:
    return Fernet(key).encrypt(plaintext.encode()).decode()


def decrypt_with_key(ciphertext: str, key: bytes) -> str:
    return Fernet(key).decrypt(ciphertext.encode()).decode()


# ── Legacy: globaler FERNET_KEY (nur für Migration bestehender Credentials) ───

def _get_legacy_key() -> bytes | None:
    key = os.environ.get("FERNET_KEY")
    if key:
        return key.encode()

    # Beim ersten Start: Schlüssel generieren und in .env speichern
    new_key = Fernet.generate_key().decode()
    env_path = Path(__file__).parent.parent / ".env"
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"FERNET_KEY={new_key}\n")
    os.environ["FERNET_KEY"] = new_key
    print("FERNET_KEY generiert und in .env gespeichert – wird nur noch für Migration benötigt.")
    return new_key.encode()


def legacy_decrypt(ciphertext: str) -> str:
    """Entschlüsselt mit dem alten globalen FERNET_KEY (nur für einmalige Migration)."""
    key = _get_legacy_key()
    if not key:
        raise ValueError("Kein FERNET_KEY in der Umgebung.")
    return Fernet(key).decrypt(ciphertext.encode()).decode()
