import requests
import os
import json

from dotenv import load_dotenv
load_dotenv()


def authenticate():
    if "PYLOAD_URL" not in os.environ:
        print("PYLOAD_URL environment variable not set")
        return None
    if "PYLOAD_USERNAME" not in os.environ:
        print("PYLOAD_USERNAME environment variable not set")
        return None
    if "PYLOAD_PASSWORD" not in os.environ:
        print("PYLOAD_PASSWORD environment variable not set")
        return None
    url = os.environ["PYLOAD_URL"]
    username = os.environ["PYLOAD_USERNAME"]
    password = os.environ["PYLOAD_PASSWORD"]
    try:
        login_payload = {
            "username": username,
            "password": password
        }
        r = requests.get(f"{url}/login", data=login_payload)
        if r.status_code == 200:
            return r.cookies
        else:
            print(f"Failed to authenticate: {r.status_code}")
            return None
    except Exception as e:
        print(e)
        return None


# Test pyload API connection and return True if successful
# Get the url from the "PYLOAD_URL" environment variable
# Get the username and passwords from the #PYLOAD_USERNAME" and "PYLOAD_PASSWORD" environment variables
def test_connection():
    cookies = authenticate()
    if cookies is None:
        print("Failed to authenticate")
        return None
    pass

def add_package(package_name: str, url_list: list, dest: str=None) -> bool:
    if "PYLOAD_URL" not in os.environ:
        print("PYLOAD_URL environment variable not set")
        return None
    if "PYLOAD_USERNAME" not in os.environ:
        print("PYLOAD_USERNAME environment variable not set")
        return None
    if "PYLOAD_PASSWORD" not in os.environ:
        print("PYLOAD_PASSWORD environment variable not set")
        return None
    url = os.environ["PYLOAD_URL"]
    username = os.environ["PYLOAD_USERNAME"]
    password = os.environ["PYLOAD_PASSWORD"]
    with requests.session() as s:
        login_payload = {
            "username": username,
            "password": password
        }
        r = s.post(f"{url}/login", data=login_payload)
        if r.status_code != 200:
            print(f"Failed to authenticate: {r.status_code}")
            return None
        try:
            payload = {
                "name": package_name,
                "links": url_list
            }
            if dest is not None:
                payload["dest"] = dest
            payloadJSON = {k: json.dumps(v) for k, v in payload.items()}
            request_url = f"{url}/api/addPackage"
            r = s.post(request_url, data=payloadJSON)
            if r.status_code == 200:
                print(f"Successfully added package {package_name} with {len(url_list)} links")
                print(r.text)
                return True
            else:
                print(f"Failed to add package {package_name}: {r.status_code}")
                print(r.text)
                return False
        except Exception as e:
            print(e)
            return False
