import os
import json
import gzip
import shutil
import argparse

import requests

try:
    from .paths import PATHS
    from .pouet_library import DEFAULT_PLATFORM_KEYS, DEFAULT_TOP_LIMIT, update_pouet_library
except ImportError:
    from paths import PATHS
    from pouet_library import DEFAULT_PLATFORM_KEYS, DEFAULT_TOP_LIMIT, update_pouet_library


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


def fetch_top_pouet_prods(paths=None, platform_keys=None, limit=DEFAULT_TOP_LIMIT, download=True):
    return update_pouet_library(
        paths=paths or PATHS,
        platform_keys=platform_keys or DEFAULT_PLATFORM_KEYS,
        limit=limit,
        download=download,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and cache top Pouet productions for Owl Arcade.")
    parser.add_argument("--platform", action="append", dest="platforms", help="Platform key to fetch, e.g. amstrad_cpc or amiga.")
    parser.add_argument("--limit", type=int, default=DEFAULT_TOP_LIMIT, help="Number of ranked prods to keep per platform.")
    parser.add_argument("--metadata-only", action="store_true", help="Build the manifest without downloading prod archives.")
    args = parser.parse_args()

    fetch_top_pouet_prods(
        platform_keys=args.platforms or DEFAULT_PLATFORM_KEYS,
        limit=args.limit,
        download=not args.metadata_only,
    )
