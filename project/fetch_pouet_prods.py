import os
import json
import requests
import gzip
import shutil

try:
    from .paths import PATHS
except ImportError:
    from paths import PATHS


def fetch_data(paths=None):
    paths = paths or PATHS
    response = requests.get('https://data.pouet.net/json.php')
    data = response.json()
    dumps = data['dumps']
    latest_date = max(dumps.keys())
    prods_url = dumps[latest_date]['prods']['url']
    filename = paths.temp / dumps[latest_date]['prods']['filename']
    response = requests.get(prods_url, stream=True)
    os.makedirs(paths.temp, exist_ok=True)
    with open(filename, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    return filename

def parse_and_classify(filename, platforms):
    with gzip.open(filename, 'rt') as f:
        data = json.load(f)
    platform_dict = {platform: [] for platform in platforms}
    for prod in data['prods']:
        for platform_key in prod['platforms']:
            platform = prod['platforms'][platform_key]
            if platform['name'] in platforms:
                platform_dict[platform['name']].append(prod)
    return platform_dict

def fetch_pouet_prods(platforms, paths=None):
    paths = paths or PATHS
    filename = fetch_data(paths)
    platform_dict = parse_and_classify(filename, platforms)
    os.makedirs(paths.db, exist_ok=True)
    with open(paths.db / 'prods.json', 'w') as f:
        json.dump(platform_dict, f, indent=2)

if __name__ == "__main__":
    fetch_pouet_prods(["Amstrad CPC", "Amiga AGA", "SNES/Super Famicom"])
