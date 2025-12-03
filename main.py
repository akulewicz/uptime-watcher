import requests
import time
import json
import os
import ssl
import smtplib
import logging
from email.message import EmailMessage

BASE_DIR = os.path.dirname(__file__)
STATUS_FILE = os.path.join(BASE_DIR, "status.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "logs/monitor.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def send_email(message, config, url):
    """Wysyła powiadomienie e-mail o zmianie statusu strony.

    message — treść wiadomości
    config — dane konfiguracyjne SMTP (host, użytkownik, hasło itd.)
    url — adres strony, której dotyczy powiadomienie
    """
    host = config["host"]
    port = config["port"]
    username = config["username"]
    password = config["password"]
    receiver = config["receiver"]

    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = receiver
    msg["Subject"] = f"Informacja dotycząca działania strony {url}"
    msg.set_content(message)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context) as server:
        server.login(username, password)
        server.send_message(msg)


def load_json(path):
    """Wczytuje dane z pliku JSON.
    Zwraca pusty słownik, jeśli plik nie istnieje (np. pierwszy start programu).
    """
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_state(path, data):
    """Zapisuje bieżący stan stron do pliku JSON."""
    with open(path, "w") as f:
        json.dump(data, f)


def get_site_status(url):
    """Sprawdza, czy witryna odpowiada kodem 200.
    Zwraca 'up' jeśli strona działa, inaczej 'down'.
    """
    try:
        response = requests.get(url, timeout=10)
        return "up" if response.status_code == 200 else "down"
    except Exception:
        return "down"


def clean_state(state, sites):
    """Usuwa ze stanu adresy stron, które zostały usunięte z config.json.
    Dzięki temu stan jest zawsze zgodny z bieżącą listą stron.
    """
    valid_urls = {site["url"] for site in sites}
    return {url: status for url, status in state.items() if url in valid_urls}


def create_status_message(url, old_status, new_status):
    """Tworzy komunikat opisujący zmianę statusu:
    - jeśli strona padła → 'Strona X nie działa.'
    - jeśli wróciła → 'Strona X już działa.'
    Jeśli zmian nie ma, zwraca None.
    """
    if old_status is None:
        if new_status == "down":
            return f"Strona {url} nie działa."
        return None

    if old_status != new_status:
        if new_status == "down":
            return f"Strona {url} nie działa."
        else:
            return f"Strona {url} już działa."

    return None  


def check_websites(config, state):
    sites = config["sites"]
    state = clean_state(state, sites)

    for site in sites:
        url = site["url"]
        previous_status = state.get(url)
        current_status = get_site_status(url)

        message = create_status_message(url, previous_status, current_status)

        if message:
            logging.info(message)
            send_email(message, config, url)

        state[url] = current_status

    save_state(STATUS_FILE, state)


if __name__ == "__main__":
    config = load_json(CONFIG_FILE)
    state = load_json(STATUS_FILE)
    check_websites(config, state)
    
