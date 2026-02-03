# traewelling-export
Export your traewelling statuses to a json or csv file.

## Installation
Just clone the repository and install the utility using `pipx`
```sh
git clone https://github.com/adridevelopsthings/traewelling-export
cd traewelling-export
pipx install .
```

## Usage
Just run
```
traewelling-export -o statuses.json
```

### Detailed Usage
```
usage: -m [-h] [-a AUTH_CONTEXT] [-t {json,csv}] [-o OUTPUT] [-c CACHE_DIRECTORY] [--oauth-client-id OAUTH_CLIENT_ID] [--purge-cache] [--disable-cache]

options:
  -h, --help            show this help message and exit
  -a, --auth-context AUTH_CONTEXT
                        If you want multiple auth contexts give a name for each one to keep them in the cache apart
  -t, --type {json,csv}
                        Output file format
  -o, --output OUTPUT   Output file path
  -c, --cache-directory CACHE_DIRECTORY
  --oauth-client-id OAUTH_CLIENT_ID
  --purge-cache
  --disable-cache
```
