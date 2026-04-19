import gzip
import json
import lzma
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse, urlunparse
from zipfile import BadZipFile, ZipFile

import requests

try:
    from .paths import PATHS
except ImportError:
    from paths import PATHS


POUET_INDEX_URL = "https://data.pouet.net/json.php"
MANIFEST_FILENAME = "pouet-library.json"
DEFAULT_PLATFORM_KEYS = ["amstrad_cpc", "amiga"]
DEFAULT_TOP_LIMIT = 50


@dataclass(frozen=True)
class PouetPlatformConfig:
    key: str
    rom_folder: str
    pouet_platforms: tuple
    media_extensions: tuple


PLATFORM_CONFIGS = {
    "amstrad_cpc": PouetPlatformConfig(
        key="amstrad_cpc",
        rom_folder="amstrad_cpc",
        pouet_platforms=("Amstrad CPC",),
        media_extensions=(".dsk", ".cpr"),
    ),
    "amiga": PouetPlatformConfig(
        key="amiga",
        rom_folder="amiga",
        pouet_platforms=("Amiga OCS/ECS", "Amiga AGA"),
        media_extensions=(".adf", ".adz", ".ipf", ".dms"),
    ),
}


def manifest_path(paths=None):
    return (paths or PATHS).db / MANIFEST_FILENAME


def fetch_pouet_index(session=None):
    session = session or requests.Session()
    response = session.get(POUET_INDEX_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def latest_prods_dump(index_data):
    latest = index_data.get("latest")
    if latest and latest.get("prods"):
        return latest["prods"]

    dumps = index_data.get("dumps", {})
    if not dumps:
        raise ValueError("Pouet index does not contain any dump metadata.")
    latest_date = max(dumps.keys())
    return dumps[latest_date]["prods"]


def fetch_latest_prods_dump(paths=None, session=None):
    paths = paths or PATHS
    session = session or requests.Session()
    dump_info = latest_prods_dump(fetch_pouet_index(session))
    paths.temp.mkdir(parents=True, exist_ok=True)
    dump_path = paths.temp / dump_info["filename"]

    if dump_path.exists() and dump_path.stat().st_size > 0:
        return dump_path, dump_info

    response = session.get(dump_info["url"], stream=True, timeout=60)
    response.raise_for_status()
    tmp_path = dump_path.with_suffix(dump_path.suffix + ".part")
    with tmp_path.open("wb") as out_file:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                out_file.write(chunk)
    tmp_path.replace(dump_path)
    return dump_path, dump_info


def load_prods_dump(dump_path):
    dump_path = Path(dump_path)
    if dump_path.suffix == ".gz":
        opener = gzip.open
    elif dump_path.suffix == ".xz":
        opener = lzma.open
    else:
        opener = open

    with opener(dump_path, "rt", encoding="utf-8") as dump_file:
        data = json.load(dump_file)
    return data.get("prods", [])


def prod_platform_names(prod):
    return {platform.get("name") for platform in prod.get("platforms", {}).values()}


def _int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def prod_rank(prod):
    return _int_value(prod.get("rank"))


def prod_sort_key(prod):
    rank = prod_rank(prod)
    ranked = rank if rank > 0 else 999999
    return (
        ranked,
        -_float_value(prod.get("popularity")),
        -_int_value(prod.get("voteup")),
        prod.get("name", "").lower(),
    )


def select_top_prods(prods, platform_names, limit=DEFAULT_TOP_LIMIT):
    platform_names = set(platform_names)
    candidates = []
    for prod in prods:
        if not prod.get("download"):
            continue
        if prod_platform_names(prod) & platform_names:
            candidates.append(prod)
    return sorted(candidates, key=prod_sort_key)[:limit]


def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "prod"


def filename_from_url(url, fallback):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    for query_name in ("filename", "file", "media"):
        if query_name in query and query[query_name]:
            filename = Path(unquote(query[query_name][0]).split(":")[-1]).name
            if filename:
                return filename

    path = unquote(parsed_url.path)
    filename = Path(path).name
    return filename or fallback


def normalize_download_url(url):
    parsed_url = urlparse(url)
    if parsed_url.netloc.lower() == "files.scene.org" and parsed_url.path.startswith("/view/"):
        parsed_url = parsed_url._replace(path="/get/" + parsed_url.path[len("/view/") :])
        return urlunparse(parsed_url)
    return url


def platform_storage_folder(paths, config, prod):
    folder_name = f"{prod.get('id', 'unknown')}-{slugify(prod.get('name', 'prod'))}"
    return paths.rom_folder(config.rom_folder) / "_pouet" / folder_name


def relative_to_rom_folder(paths, config, file_path):
    return Path(file_path).resolve().relative_to(paths.rom_folder(config.rom_folder).resolve()).as_posix()


def build_manifest_entry(prod, config, paths):
    prod_folder = platform_storage_folder(paths, config, prod)
    download_url = prod.get("download")
    archive_name = filename_from_url(download_url, f"{prod.get('id', 'prod')}.bin")
    archive_path = prod_folder / archive_name
    group_names = [group.get("name") for group in prod.get("groups", []) if group.get("name")]

    return {
        "id": str(prod.get("id")),
        "title": prod.get("name") or f"Pouet #{prod.get('id')}",
        "filename": [relative_to_rom_folder(paths, config, archive_path)],
        "source": "pouet",
        "launchable": False,
        "rank": prod_rank(prod),
        "popularity": _float_value(prod.get("popularity")),
        "voteup": _int_value(prod.get("voteup")),
        "platforms": sorted(prod_platform_names(prod)),
        "groups": group_names,
        "download": {
            "url": download_url,
            "local_archive": relative_to_rom_folder(paths, config, archive_path),
            "status": "pending",
        },
        "launch": {
            "status": "pending",
            "media": None,
        },
    }


def download_artifact(url, destination, session=None):
    url = normalize_download_url(url)
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        return {"ok": False, "status": f"unsupported URL scheme: {parsed_url.scheme}"}

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0 and cached_artifact_is_usable(destination):
        return {"ok": True, "status": "cached", "path": destination}

    session = session or requests.Session()
    response = session.get(url, stream=True, timeout=60)
    response.raise_for_status()

    content_filename = filename_from_content_disposition(response.headers.get("Content-Disposition"))
    if content_filename:
        destination = destination.parent / content_filename

    tmp_path = destination.with_suffix(destination.suffix + ".part")
    with tmp_path.open("wb") as out_file:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                out_file.write(chunk)
    tmp_path.replace(destination)
    return {"ok": True, "status": "downloaded", "path": destination}


def filename_from_content_disposition(value):
    if not value:
        return None
    match = re.search(r'filename="?([^";]+)"?', value)
    if not match:
        return None
    return Path(unquote(match.group(1))).name


def cached_artifact_is_usable(path):
    if path.suffix.lower() != ".zip":
        return True
    try:
        with ZipFile(path, "r") as archive:
            return archive.testzip() is None
    except BadZipFile:
        path.unlink(missing_ok=True)
        return False


def _zip_media_members(archive_path, media_extensions):
    with ZipFile(archive_path, "r") as archive:
        return [
            member
            for member in archive.namelist()
            if not member.endswith("/") and Path(member).suffix.lower() in media_extensions
        ]


def media_member_sort_key(member_name):
    name = Path(member_name).name.lower()
    score = 0
    if "disk 1" in name or "disc 1" in name or "dsk1" in name:
        score -= 10
    if "side a" in name or "face a" in name:
        score -= 5
    if "side b" in name or "face b" in name:
        score += 5
    if "loader" in name or "boot" in name:
        score -= 3
    return score, name


def _extract_zip_media(archive_path, member_name, destination_folder):
    destination_folder.mkdir(parents=True, exist_ok=True)
    media_path = destination_folder / Path(member_name).name
    if media_path.exists() and media_path.stat().st_size > 0:
        return media_path

    with ZipFile(archive_path, "r") as archive:
        with archive.open(member_name) as source, media_path.open("wb") as target:
            shutil.copyfileobj(source, target)
    return media_path


def prepare_launch_media(paths, config, archive_path):
    suffix = archive_path.suffix.lower()
    if suffix in config.media_extensions:
        return {
            "launchable": True,
            "status": "ready",
            "media_path": archive_path,
        }

    if suffix != ".zip":
        return {
            "launchable": False,
            "status": f"unsupported archive type: {suffix or 'unknown'}",
            "media_path": None,
        }

    try:
        media_members = _zip_media_members(archive_path, config.media_extensions)
    except BadZipFile:
        return {"launchable": False, "status": "invalid zip archive", "media_path": None}

    if not media_members:
        return {"launchable": False, "status": "zip does not contain launchable media", "media_path": None}

    media_members.sort(key=media_member_sort_key)
    media_path = _extract_zip_media(archive_path, media_members[0], archive_path.parent / "media")
    return {
        "launchable": True,
        "status": "ready",
        "media_path": media_path,
    }


def download_and_prepare_prod(paths, config, prod, session=None):
    entry = build_manifest_entry(prod, config, paths)
    archive_path = paths.rom_folder(config.rom_folder) / entry["download"]["local_archive"]

    try:
        download_result = download_artifact(entry["download"]["url"], archive_path, session=session)
    except requests.RequestException as exc:
        entry["download"]["status"] = f"failed: {exc}"
        entry["launch"]["status"] = "download failed"
        return entry

    entry["download"]["status"] = download_result["status"]
    if not download_result["ok"]:
        entry["launch"]["status"] = download_result["status"]
        return entry

    archive_path = download_result["path"]
    entry["download"]["local_archive"] = relative_to_rom_folder(paths, config, archive_path)
    launch_info = prepare_launch_media(paths, config, archive_path)
    entry["launchable"] = launch_info["launchable"]
    entry["launch"]["status"] = launch_info["status"]
    if launch_info["media_path"] is not None:
        entry["launch"]["media"] = relative_to_rom_folder(paths, config, launch_info["media_path"])
        entry["filename"] = [entry["launch"]["media"]]
    return entry


def write_manifest(manifest, paths=None):
    path = manifest_path(paths)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)
    return path


def load_manifest(paths=None):
    path = manifest_path(paths)
    if not path.exists():
        return {"platforms": {}}
    with path.open("r", encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def load_platform_entries(paths, platform_key):
    manifest = load_manifest(paths)
    entries = manifest.get("platforms", {}).get(platform_key, [])
    config = PLATFORM_CONFIGS.get(platform_key)
    if config is None:
        return entries

    usable_entries = []
    for entry in entries:
        filenames = entry.get("filename") or []
        if not filenames:
            continue
        local_path = paths.rom_folder(config.rom_folder) / filenames[0]
        if local_path.exists():
            usable_entries.append(entry)
    return usable_entries


def update_pouet_library(paths=None, platform_keys=None, limit=DEFAULT_TOP_LIMIT, download=True, dump_path=None, session=None):
    paths = paths or PATHS
    platform_keys = platform_keys or DEFAULT_PLATFORM_KEYS
    session = session or requests.Session()

    if dump_path is None:
        dump_path, dump_info = fetch_latest_prods_dump(paths, session=session)
    else:
        dump_path = Path(dump_path)
        dump_info = {"filename": dump_path.name, "url": str(dump_path), "size_in_bytes": dump_path.stat().st_size}

    prods = load_prods_dump(dump_path)
    manifest = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "index_url": POUET_INDEX_URL,
            "dump": dump_info,
        },
        "platforms": {},
    }

    for platform_key in platform_keys:
        config = PLATFORM_CONFIGS[platform_key]
        selected_prods = select_top_prods(prods, config.pouet_platforms, limit)
        entries = []
        for prod in selected_prods:
            if download:
                entry = download_and_prepare_prod(paths, config, prod, session=session)
            else:
                entry = build_manifest_entry(prod, config, paths)
                entry["download"]["status"] = "not downloaded"
                entry["launch"]["status"] = "not prepared"
            entries.append(entry)
        manifest["platforms"][platform_key] = entries

    write_manifest(manifest, paths)
    return manifest
