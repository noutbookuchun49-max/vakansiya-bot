#!/usr/bin/env python3
"""
create_session.py

Simple helper to generate a Telethon StringSession locally.

Usage (locally):
1) Install Telethon: pip install telethon
2) Run: python create_session.py
3) Enter your API_ID and API_HASH when prompted.
4) Follow the login flow (phone number + code). The script will print a new session string.
5) Copy the printed session string into your repository's GitHub Secrets as TELEGRAM_SESSION.

Do NOT run this on a public CI. Run it locally on your machine or a trusted environment.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession


def main():
    try:
        api_id_raw = input("API_ID: ").strip()
        api_id = int(api_id_raw)
    except Exception:
        print("API_ID must be an integer. Aborting.")
        return

    api_hash = input("API_HASH: ").strip()
    if not api_hash:
        print("API_HASH is required. Aborting.")
        return

    print("Starting Telegram client. You will be asked for your phone number and login code.")
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("Logged in as:", getattr(client, 'get_me') and None)
        # Save and print the session string
        session_str = client.session.save()
        print("\nCopy the following SESSION STRING and add it to GitHub Secrets -> TELEGRAM_SESSION:")
        print(session_str)


if __name__ == '__main__':
    main()
