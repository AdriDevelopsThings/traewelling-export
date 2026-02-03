from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256
from random import choice
from string import ascii_letters
from time import time
from typing import Optional, TypedDict
from urllib.parse import quote

import requests
import url64
from charset_normalizer import from_bytes

from traewelling_export.cache import Cache
from traewelling_export.traewelling.code_recv import start_code_recv

OAUTH_PORT = 45691
OAUTH_REDIRECT_URI = f"http://localhost:{OAUTH_PORT}/callback"


class Auth(ABC):
    @abstractmethod
    def get_token(self) -> str:
        pass


class TokenAuth(Auth):
    def __init__(self, token: str):
        self.__token = token

    def get_token(self) -> str:
        return self.__token


class TokenData(TypedDict):
    token_type: str
    expires_in: int
    access_token: str


@dataclass
class Token:
    access_token: str
    expires: int

    @classmethod
    def from_token_data(cls, token_data: TokenData) -> "Token":
        return Token(
            access_token=token_data["access_token"],
            expires=int(time() + token_data["expires_in"]),
        )

    @classmethod
    def from_dict(cls, d: dict) -> "Token":
        return Token(access_token=d["access_token"], expires=d["expires"])

    def to_dict(self) -> dict:
        return {"access_token": self.access_token, "expires": self.expires}


class OAuth2(Auth):
    def __init__(
        self,
        cache: Cache,
        auth_ctx: str,
        client_id: str,
        authorize_url: str,
        token_url: str,
    ):
        self.__auth_ctx = auth_ctx
        self.__client_id = client_id
        self.__cache = cache
        self.__authorize_url = authorize_url
        self.__token_url = token_url

        self.__token: Optional[Token] = None

    def __get_new_code(self) -> tuple[str, str]:
        code_verifier: str = "".join([choice(ascii_letters) for i in range(64)])
        code_challenge = url64.encode(sha256(code_verifier.encode("utf-8")).digest())

        authorize_url = (
            self.__authorize_url
            + f"?response_type=code&client_id={self.__client_id}&code_challenge={code_challenge}&code_challenge_method=S256&redirect_uri={quote(OAUTH_REDIRECT_URI)}"
        )
        print("Open this page in the browser to authorize this application:")
        print(authorize_url)
        return code_verifier, start_code_recv(OAUTH_PORT)

    def __get_token(self, code: str, code_verifier: str) -> TokenData:
        response = requests.post(
            self.__token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": self.__client_id,
                "code": code,
                "redirect_uri": OAUTH_REDIRECT_URI,
                "code_verifier": code_verifier,
            },
        )
        response.raise_for_status()
        return response.json()

    def get_token(self) -> str:
        if self.__token is None:
            cached_token = self.__cache.get(
                "traewelling", f"token_{self.__auth_ctx}", dict
            )
            if cached_token:
                self.__token = Token.from_dict(cached_token)

        if self.__token is not None and self.__token.expires > time():
            return self.__token.access_token

        code_verifier, code = self.__get_new_code()
        token = self.__get_token(code, code_verifier)
        self.__token = Token.from_token_data(token)
        self.__cache.set(
            "traewelling", f"token_{self.__auth_ctx}", self.__token.to_dict()
        )
        return self.__token.access_token
