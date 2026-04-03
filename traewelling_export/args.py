from argparse import ArgumentParser
from datetime import datetime

from platformdirs import user_cache_dir

APP_NAME = "traewelling-export"
APP_AUTHOR = "AdriDevelopsThings"

parser = ArgumentParser()
parser.add_argument(
    "-a",
    "--auth-context",
    type=str,
    default="default",
    help="If you want multiple auth contexts give a name for each one to keep them in the cache apart",
)
parser.add_argument("--skip-auth", action="store_true")
parser.add_argument(
    "-u",
    "--username",
    type=str,
    help="Username of user who should be downloaded. Username is automatically determined if not set.",
)
parser.add_argument(
    "-l",
    "--limit",
    type=int,
    help="Limit the number of statuses that should be exported.",
)
parser.add_argument(
    "--until",
    type=lambda s: datetime.strptime(s, "%Y-%m-%d").astimezone(),
    help="Export only statuses that are newer that the supplied date with the format YYYY-MM-DD.",
)
parser.add_argument(
    "-t", "--type", help="Output file format", choices=["json", "csv"], default="json"
)
parser.add_argument(
    "-o", "--output", help="Output file path", default="USERNAME.SUFFIX"
)
parser.add_argument(
    "-c",
    "--cache-directory",
    default=user_cache_dir(APP_NAME, APP_AUTHOR),
)
parser.add_argument("--oauth-client-id", type=int, default=153)
parser.add_argument("--purge-cache", action="store_true")
parser.add_argument("--disable-cache", action="store_true")
