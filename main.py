import requests
import time
import json
import os
import ssl
import smtplib
from email.message import EmailMessage

def send_email(message, config):
    host = config["host"]
    port = config["port"]
    username = config["username"]
    password = config["password"]
    receiver = config["receiver"]

    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = receiver
    msg["Subject"] = "Informacja dotycząca działania strony"
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

def check_websites():
    config = load_json("config.json")
    state = load_json("status.json")
    sites = config['sites']

    for site in sites:
        url = site['url']
        try:
            response = requests.get(url, timeout=10)
            current_status = "up" if response.status_code == 200 else "down"
        except Exception:
            current_status = "down"

        if url not in state:
            if current_status == "down":
                send_email(f'Strona  {url} nie działa', config)
            state[url] = current_status
            continue
        
        if current_status != state[url]:
            if current_status == "down":
                send_email(f"Strona {url} nie działa", config)
            else:
                send_email(f"Strona {url} już działa", config)
    save_state("status.json", state)


if __name__ == "__main__":
    while True:
        check_websites()
        time.sleep(60)