import requests
import time
import json
import os
import ssl
import smtplib
import logging
from email.message import EmailMessage

logging.basicConfig(
    filename="logs/monitor.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def send_email(message, config, url):
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
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save_state(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def get_site_status(url):
    try:
        response = requests.get(url, timeout=10)
        return "up" if response.status_code == 200 else "down"
    except Exception:
        return "down"


def clean_state(state, sites):
    valid_urls = {site["url"] for site in sites}
    return {url: status for url, status in state.items() if url in valid_urls}


def create_status_message(url, old_status, new_status):
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

    save_state("status.json", state)


if __name__ == "__main__":
    config = load_json("config.json")
    while True:
        state = load_json("status.json")
        check_websites(config, state)
        time.sleep(60)
