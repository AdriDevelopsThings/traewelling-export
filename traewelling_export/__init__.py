from datetime import datetime
from json import dump
from os import environ
from typing import Any, Optional

from traewelling_export.args import parser
from traewelling_export.cache import Cache
from traewelling_export.traewelling import (TRAEWELLING_OAUTH_AUTHORIZE_URL,
                                            TRAEWELLING_OAUTH_TOKEN_URL,
                                            TraewellingClient)
from traewelling_export.traewelling.auth import Auth, OAuth2, TokenAuth


def write_csv(headers: list[Any], values: list[list[Any]], file):
    def __write_csv_values(values: list[Any], file):
        file.write(",".join(['"' + str(v) + '"' for v in values]) + "\n")

    __write_csv_values(headers, file)
    for v in values:
        __write_csv_values(v, file)


def write_output(statuses: list[dict], file, type: str) -> None:
    statuses = [
        {
            "id": s["id"],
            "body": s["body"],
            "createdAt": s["createdAt"],
            "category": s["train"]["category"],
            "line": s["train"]["lineName"],
            "number": s["train"]["number"],
            "distance": s["train"]["distance"],
            "duration": s["train"]["duration"],
            "origin": s["train"]["origin"]["name"],
            "departurePlanned": s["train"]["origin"]["departurePlanned"],
            "departureReal": s["train"]["origin"]["departureReal"],
            "destination": s["train"]["destination"]["name"],
            "arrivalPlanned": s["train"]["destination"]["arrivalPlanned"],
            "arrivalReal": s["train"]["destination"]["arrivalReal"],
            "event": s["event"]["name"] if s["event"] else None,
        }
        for s in statuses
    ]

    if type == "json":
        dump(statuses, file)
    elif type == "csv":
        headers = list(statuses[0].keys())
        write_csv(headers, [list(v.values()) for v in statuses], file)
    else:
        raise ValueError(f"Invalid output type {type}")


def main() -> None:
    args = parser.parse_args()
    cache = Cache(args.cache_directory, args.disable_cache)

    if args.purge_cache:
        cache.purge()
        print("Cache purged")
        return

    auth: Optional[Auth] = None
    if environ.get("TRAEWELLING_TOKEN"):
        auth = TokenAuth(environ["TRAEWELLING_TOKEN"])
    elif not args.skip_auth:
        auth = OAuth2(
            cache,
            args.auth_context,
            args.oauth_client_id,
            TRAEWELLING_OAUTH_AUTHORIZE_URL,
            TRAEWELLING_OAUTH_TOKEN_URL,
        )

    traewelling = TraewellingClient(auth)

    username: Optional[str] = args.username
    if not username:
        if args.skip_auth:
            raise Exception(
                "Authentication is disabled but no username is supplied, I couldn't guess who you are."
            )
        me = traewelling.get_me()
        username: str = me["username"]

    statuses: list[dict] = []
    page = 1
    print("Fetching statuses...")
    while True:
        print(f"\033[KPage {page}", end="\r", flush=True)
        cached_page: Optional[list[dict]] = cache.get(
            f"{username}-page", str(page), list
        )
        cached = False
        if cached_page and page != 1:
            cached = True
            statuses.extend(cached_page)
        elif not cached_page and page == 1:
            cache.purge(nmspc=f"{username}-page")

        if not cached:
            data = traewelling.get_user_statuses(username, page=page)
            if not data:
                break

            if (
                cached_page
                and page == 1
                and (
                    len(cached_page) != len(data)
                    or any(
                        [c["id"] != data[i]["id"] for (i, c) in enumerate(cached_page)]
                    )
                )
            ):
                # first page real and cached don't match, invalidate cache
                cache.purge(nmspc=f"{username}-page")

            cache.set(f"{username}-page", str(page), data)
            statuses.extend(data)

        if args.limit and len(statuses) >= args.limit:
            statuses = statuses[: len(statuses)]
            break

        if (
            args.until
            and len(statuses) > 0
            and datetime.fromisoformat(statuses[-1]["createdAt"]) < args.until
        ):
            statuses = [
                status
                for status in statuses
                if datetime.fromisoformat(status["createdAt"]) >= args.until
            ]
            break
        page += 1

    print()

    output_type = args.type
    output_path = args.output.replace("SUFFIX", output_type).replace(
        "USERNAME", username
    )

    with open(output_path, "w") as file:
        write_output(statuses, file, output_type)
