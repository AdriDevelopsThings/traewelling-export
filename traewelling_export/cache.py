from hashlib import blake2s
from json import dump, load
from os import listdir, mkdir, remove
from os.path import exists, join
from typing import Any, Optional, Type, TypeAlias, TypeVar

K: TypeAlias = str | dict[str, Any]
O = TypeVar("O", str, dict, list)


class Cache:
    def __init__(self, dir: str, disable_cache: bool):
        self.__dir = dir
        self.__disable_cache = disable_cache
        if not exists(dir):
            mkdir(dir)

    def __get_key(self, nmspc: str, k: K) -> str:
        if isinstance(k, str):
            key = k
        elif isinstance(k, dict):
            key = ""
            for key, value in k.items():
                key += f"{key}={value}"
        else:
            raise ValueError(f"Cache key {k} is of type {type(k)} which is invalid")

        hashed_key = blake2s(key.encode("utf-8")).hexdigest()
        return f"{nmspc}_{hashed_key}"

    def __key_path(self, key: str) -> str:
        return join(self.__dir, key)

    def get(self, nmspc: str, k: K, typ: Type[O]) -> Optional[O]:
        path = self.__key_path(self.__get_key(nmspc, k))
        if not exists(path) or self.__disable_cache:
            return None
        with open(path) as file:
            if typ is str:
                return file.read()  # type: ignore
            elif typ is dict or typ is list:
                return load(file)
            else:
                raise ValueError(f"Invalid typ {typ}")

    def set(self, nmspc: str, k: K, c: O) -> None:
        if self.__disable_cache:
            return
        path = self.__key_path(self.__get_key(nmspc, k))
        with open(path, "w") as file:
            if isinstance(c, str):
                file.write(c)
            elif isinstance(c, dict) or isinstance(c, list):
                dump(c, file)
            else:
                raise ValueError(f"Invalid type of content: {type(c)}")

    def purge(self, nmspc: Optional[str] = None) -> None:
        for file in listdir(self.__dir):
            if not nmspc or file.startswith(f"{nmspc}_"):
                remove(join(self.__dir, file))
