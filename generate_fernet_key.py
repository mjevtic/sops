#!/usr/bin/env python3
"""
Generate a valid Fernet key for SupportOps Automator encryption.
This script generates a URL-safe base64-encoded 32-byte key for use with Fernet encryption.
"""
from cryptography.fernet import Fernet

def generate_fernet_key():
    """Generate a new Fernet key and print it."""
    key = Fernet.generate_key()
    print("\nGenerated Fernet key:")
    print(key.decode())
    print("\nUse this key as the value for ENCRYPTION_KEY in your environment variables.")
    print("Make sure to keep this key secure and consistent across deployments.")

if __name__ == "__main__":
    generate_fernet_key()
