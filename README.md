# traewelling-export
Export your traewelling statuses to a json or csv file.

## Installation
You'll need python version 3.7 or higher. Then you have to install the pip requirements:
```sh
pip install -r requirements.txt
```

## Run
Just generate an access token [here](https://traewelling.de/settings/security/api-tokens). Then run
```sh
TRAEWELLING_TOKEN=YOUR_GENERATED_TRAEWELLING_TOKEN_HERE python main.py
```
If you don't want to write the token in the shell you can also create an `.env` file containing
```
TRAEWELLING_TOKEN=YOUR_GENERATED_TRAEWELLING_TOKEN_HERE
```