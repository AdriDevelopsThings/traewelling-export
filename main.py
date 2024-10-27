from argparse import ArgumentParser
from os import environ, mkdir, listdir, remove
from os.path import join, exists
from time import sleep
from json import dump, load
from platformdirs import user_cache_dir
import gzip
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass

parser = ArgumentParser()
parser.add_argument(
    "-t", "--type", help="Output file format", choices=["json", "csv"], default="json"
)
parser.add_argument("-o", "--output", help="Output file path", default="output.SUFFIX")
parser.add_argument(
    "-c",
    "--cache-directory",
    default=user_cache_dir("traewelling-export", "adridevelopsthings"),
)
parser.add_argument("--disable-cache", action="store_true")

TOKEN = environ.get("TRAEWELLING_TOKEN")

TRAEWELLING_URL = "https://traewelling.de"
TRAEWELLING_ME_URL = TRAEWELLING_URL + "/api/v1/auth/user"
TRAEWELLING_STATUSES_URL = TRAEWELLING_URL + "/api/v1/user/USERNAME/statuses"


class Cache:
    def __init__(self, cache_directory: str, disable_cache: bool):
        self.cache_directory = cache_directory
        self.disable_cache = disable_cache or not cache_directory
        if not self.disable_cache and not exists(cache_directory):
            mkdir(cache_directory)

    def __get_page_path(self, page_nr: int) -> str:
        return join(self.cache_directory, f"page_{page_nr}.json.gz")

    def store_page(self, page_nr: int, statuses):
        if self.disable_cache:
            return
        with gzip.open(self.__get_page_path(page_nr), "wt") as file:
            dump(statuses, file)

    def get_page(self, page_nr: int) -> list | None:
        if self.disable_cache:
            return None
        path = self.__get_page_path(page_nr)
        if not exists(path):
            return None
        with gzip.open(path, "rt") as file:
            return load(file)

    def clear_cache(self):
        if self.disable_cache:
            return None
        for entry in listdir(self.cache_directory):
            if not entry.startswith("page") or not entry.endswith(".json.gz"):
                continue
            path = join(self.cache_directory, entry)
            remove(path)


def __request(url, token):
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if response.status_code == 429:
        retry = int(response.headers.get("retry-after"))
        print("Waiting for end of rate limit...", end="\r", flush=True)
        sleep(retry + 1)
        return __request(url, token)
    response.raise_for_status()
    return response.json()


def write_csv(headers, values, file):
    def __write_csv_values(values, file):
        file.write(",".join(['"' + str(v) + '"' for v in values]) + "\n")

    __write_csv_values(headers, file)
    for v in values:
        __write_csv_values(v, file)


def write_output(statuses, file, type):
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
        headers = statuses[0].keys()
        write_csv(headers, [v.values() for v in statuses], file)
    else:
        raise Exception(f"Invalid output type {type}")


if __name__ == "__main__":
    args = parser.parse_args()
    output_type = args.type
    output_path = args.output.replace("SUFFIX", output_type)
    cache = Cache(args.cache_directory, args.disable_cache)

    if not TOKEN:
        print("Environment variable 'TRAEWELLING_TOKEN' must be set.")
        exit(1)

    me = __request(TRAEWELLING_ME_URL, TOKEN)
    username = me["data"]["username"]

    statuses = []
    page = 1
    print("Fetching statuses...")
    while True:
        print(f"\033[KPage {page}", end="\r", flush=True)
        cached_page = cache.get_page(page)
        if cached_page and page != 1:
            statuses.extend(cached_page)
            page += 1
            continue
        elif not cached_page and page == 1:
            cache.clear_cache()
        response = __request(
            TRAEWELLING_STATUSES_URL.replace("USERNAME", username) + f"?page={page}",
            TOKEN,
        )
        if not response["data"]:
            break

        if (
            cached_page
            and page == 1
            and (
                len(cached_page) != len(response["data"])
                or any(
                    [
                        c["id"] != response["data"][i]["id"]
                        for (i, c) in enumerate(cached_page)
                    ]
                )
            )
        ):
            # first page real and cached don't match, invalidate cache
            cache.clear_cache()

        cache.store_page(page, response["data"])
        statuses.extend(response["data"])
        page += 1
    print()
    with open(output_path, "w") as file:
        write_output(statuses, file, output_type)
