from time import sleep
from typing import Any, Optional

import requests

from traewelling_export.traewelling.auth import Auth

TRAEWELLING_BASE = "https://traewelling.de"
TRAEWELLING_OAUTH_AUTHORIZE_URL = TRAEWELLING_BASE + "/oauth/authorize"
TRAEWELLING_OAUTH_TOKEN_URL = TRAEWELLING_BASE + "/oauth/token"
TRAEWELLING_ME_URL = TRAEWELLING_BASE + "/api/v1/auth/user"
TRAEWELLING_USER_STATUSES_URL = TRAEWELLING_BASE + "/api/v1/user/{USERNAME}/statuses"


class TraewellingClient:
    def __init__(self, auth: Auth) -> None:
        self.__auth = auth

    def __get_auth_headers(self) -> dict[str, str]:
        token = self.__auth.get_token()
        return {"Authorization": f"Bearer {token}"}

    def __http_get(self, url: str, params: Optional[dict[str, Any]] = None) -> dict:
        response = requests.get(url, params=params, headers=self.__get_auth_headers())
        if response.status_code == 429:
            retry = int(response.headers["retry-after"])
            print("Waiting for end of rate limit...", end="\r", flush=True)
            sleep(retry + 1)
        response.raise_for_status()
        return response.json()

    def get_me(self) -> dict:
        return self.__http_get(TRAEWELLING_ME_URL)["data"]

    def get_user_statuses(
        self, username: str, page: Optional[int] = None
    ) -> list[dict]:
        return self.__http_get(
            TRAEWELLING_USER_STATUSES_URL.replace("{USERNAME}", username),
            params={"page": page} if page else None,
        )["data"]
