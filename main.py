import tls_client
import requests
import time
import random
import string
import json
from threading import Thread
from raducord import *

site_key = "6LeHZ6UUAAAAAKat_YS--O2tj_by3gv3r_l03j9d"
site_url = "https://webshare.io"

with open('config.json', 'r') as f:
    config = json.load(f)

api_key = config["capsolverkey"]
threads = config["threads"]
proxyless = config["proxyless"]

def generate_random_email():
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"{username}@gmail.com"

def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))

def capsolver():
    payload = {
        "clientKey": api_key,
        "task": {
            "type": 'ReCaptchaV2TaskProxyLess',
            "websiteKey": site_key,
            "websiteURL": site_url
        }
    }
    res = requests.post("https://api.capsolver.com/createTask", json=payload)
    resp = res.json()
    task_id = resp.get("taskId")
    if not task_id:
        Logger.failed("Failed,Solving,Captcha")
        return None
    Logger.captcha(f"Solved,Captcha,{task_id}")

    while True:
        time.sleep(3)
        payload = {"clientKey": api_key, "taskId": task_id}
        res = requests.post("https://api.capsolver.com/getTaskResult", json=payload)
        resp = res.json()
        status = resp.get("status")
        if status == "ready":
            return resp.get("solution", {}).get('gRecaptchaResponse')
        if status == "failed" or resp.get("errorId"):
            Logger.failed("Failed,Solving,Captcha")
            return None

def register_account(proxy=None):
    token = capsolver()
    if not token:
        Logger.failed("Failed,Solving,Captcha")
        return

    email = generate_random_email()
    password = generate_random_password()

    session = tls_client.Session(
        client_identifier="chrome112",
        random_tls_extension_order=True
    )

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://proxy2.webshare.io",
        "Referer": "https://proxy2.webshare.io/",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    data = {
        "email": email,
        "password": password,
        "recaptcha": token,
        "tos_accepted": True
    }

    if proxy:
        response = session.post(
            "https://proxy.webshare.io/api/v2/register/",
            headers=headers,
            json=data,
            proxy=f"http://{proxy}"
        )
    else:
        response = session.post(
            "https://proxy.webshare.io/api/v2/register/",
            headers=headers,
            json=data
        )

    if response.status_code != 200:
        Logger.failed("Failed,Registering,Failed")
        return

    Logger.success(f"Registered,Account,{email}")

    registration_result = response.json()
    access_token = registration_result.get("token")
    if not access_token:
        print("A patch has  probably been done")
        return

    proxies_response = session.get(
        "https://proxy.webshare.io/api/v2/proxy/list/",
        headers={"Authorization": f"Token {access_token}"},
        params={"mode": "direct"}
    )

    if proxies_response.status_code != 200:
        Logger.failed(f"Failed,Downloading,Proxies")
        return

    proxies = proxies_response.json().get("results", [])
    if not proxies:
        print(proxies_response.text)
        return

    with open("outputtedproxies.txt", "a") as file:
        for proxy in proxies:
            ip = proxy["proxy_address"]
            port = proxy["port"]
            user = proxy["username"]
            passw = proxy["password"]
            file.write(f"{user}:{passw}@{ip}:{port}\n")

    Logger.info(f"Generated,Proxies,10")

def worker(proxy=None):
    while True:
        register_account(proxy)

def main():
    proxies = []
    if not proxyless:
        with open('proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f]

    threads_list = []
    for i in range(threads):
        proxy = proxies[i % len(proxies)] if proxies else None
        t = Thread(target=worker, args=(proxy,))
        t.start()
        threads_list.append(t)

    for t in threads_list:
        t.join()

if __name__ == "__main__":
    main()
