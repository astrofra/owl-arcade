from pathlib import Path

from tqdm import tqdm
from xmltodict import parse

try:
    from .classic_levenshtein import levenshtein_distance
    from .paths import PATHS
    from .pouet_library import load_platform_entries
except ImportError:
    from classic_levenshtein import levenshtein_distance
    from paths import PATHS
    from pouet_library import load_platform_entries


EXCLUDED_FILENAMES = {".gitkeep", ".git", ".gitignore", "_pouet"}


def is_excluded(filename):
    return filename in EXCLUDED_FILENAMES


def beautify_filename(title):
    for extension in [".zip", ".adf", ".adz", ".ipf", ".dsk", ".cpr", ".sna", ".cdt", ".lha"]:
        if title.lower().endswith(extension):
            title = title[: -len(extension)]

    if title.find("(") > -1 and title.rfind(")") > -1:
        title_detail = title[title.rfind("("):title.rfind(")") + 1]
        title_detail = title_detail.replace("(", "").replace(")", "").strip().lower()
        if title_detail.find("disk") > -1 and title_detail.find("of") > -1:
            title = title[:title.rfind("(")]

    if title.find(" ") == -1:
        if title.find("-") > -1:
            title = title.replace("-", " ")
        elif title.find("_") > -1:
            title = title.replace("_", " ")
        title = title.capitalize()

    return title


def get_rom_title(game):
    return game.get("title")


def parse_generic_zip_games(rom_path):
    rom_path = Path(rom_path)
    rom_path.mkdir(parents=True, exist_ok=True)

    rom_list = sorted(path.name for path in rom_path.iterdir() if path.is_file())
    game_list = []

    for i in tqdm(range(len(rom_list))):
        rom_filename = rom_list[i]
        if not is_excluded(rom_filename):
            game_list.append({"title": beautify_filename(rom_filename), "filename": [rom_filename]})

    game_list.sort(key=get_rom_title)
    return game_list


def parse_amiga_games(paths=None):
    paths = paths or PATHS
    print("Building Amiga Game List")
    rom_path = paths.rom_folder("amiga")
    rom_path.mkdir(parents=True, exist_ok=True)

    rom_list = sorted(path.name for path in rom_path.iterdir() if not is_excluded(path.name))
    game_list = []

    rom_idx = 0
    while rom_idx < len(rom_list):
        group = [rom_list[rom_idx]]
        other_rom_idx = rom_idx + 1
        while other_rom_idx < len(rom_list) and levenshtein_distance(rom_list[rom_idx], rom_list[other_rom_idx]) <= 2:
            group.append(rom_list[other_rom_idx])
            other_rom_idx += 1
        game_list.append({"title": beautify_filename(rom_list[rom_idx]), "filename": group})
        rom_idx = other_rom_idx

    return game_list + load_platform_entries(paths, "amiga")


def parse_apple_2_games(paths=None):
    paths = paths or PATHS
    print("Building Apple // Game List")
    return parse_generic_zip_games(paths.rom_folder("apple_2"))


def parse_trs_80_games(paths=None):
    paths = paths or PATHS
    print("Building TANDY TRS 80 Game List")
    return parse_generic_zip_games(paths.rom_folder("tandy_trs_80"))


def parse_amstrad_cpc_games(paths=None):
    paths = paths or PATHS
    print("Building AMSTRAD CPC Game List")
    return parse_generic_zip_games(paths.rom_folder("amstrad_cpc")) + load_platform_entries(paths, "amstrad_cpc")


def parse_sega_megadrive_games(paths=None):
    paths = paths or PATHS
    print("Building SEGA MEGADRIVE Game List")
    return parse_generic_zip_games(paths.rom_folder("sega_megadrive"))


def parse_mame_games(paths=None):
    paths = paths or PATHS
    print("Building MAME Game List")

    if not paths.mame_xml.exists():
        print(f"MAME metadata file is missing: {paths.mame_xml}")
        return []

    rom_path = paths.rom_folder("mame")
    rom_path.mkdir(parents=True, exist_ok=True)

    with paths.mame_xml.open() as f:
        mame_list = parse(f.read())

    rom_list = sorted(path.name for path in rom_path.iterdir())
    game_list = []

    for rom_idx in tqdm(range(len(rom_list))):
        rom_filename = rom_list[rom_idx]
        if is_excluded(rom_filename):
            continue

        rom_name = rom_filename.replace(".zip", "")
        for key in mame_list:
            entries = mame_list[key].get("game", [])
            if isinstance(entries, dict):
                entries = [entries]
            for entry in entries:
                if str(entry.get("@name")) == rom_name:
                    game_list.append({"title": str(entry.get("description", rom_name)), "filename": [rom_filename]})

    game_list.sort(key=get_rom_title)
    return game_list
