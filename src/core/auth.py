import requests
from typing import Optional
from .config import PING_FED_URL, KGW_CLIENT_ID, KGW_CLIENT_SECRET

class AuthManager:
    def __init__(self):
        self.access_token: Optional[str] = None

    def get_access_token(self) -> bool:
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': KGW_CLIENT_ID,
            'client_secret': KGW_CLIENT_SECRET
        }

        try:
            response = requests.post(
                PING_FED_URL,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )

            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return True
            return False
        except Exception as e:
            print(f"Token error: {e}")
            return False

    def ensure_authenticated(self) -> bool:
        if not self.access_token:
            return self.get_access_token()
        return True