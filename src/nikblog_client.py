import os
import requests

session = requests.Session()

def login() -> None:
    response = session.post(
        f"{os.environ['NIKBLOG_API_URL']}/auth/login",
        json={"email": os.environ["NIKBLOG_ADMIN_EMAIL"], "password": os.environ["NIKBLOG_ADMIN_PASSWORD"]},
    )
    response.raise_for_status()