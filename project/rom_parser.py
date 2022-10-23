from os import getcwd, path, pardir, listdir
from tqdm import tqdm
from xmltodict import parse
from classic_levenshtein import levenshtein_distance
from xmltodict import parse


def is_excluded(filename):
    excluded_filenames = ['.gitkeep', '.git', '.gitignore']
    if filename in excluded_filenames:
        return True
    return False


def beautify_filename(title):
    for ext_list in ['.zip', '.ZIP', '.Zip']:
        title = title.replace(ext_list, '')
    for ext_list in ['.adf', '.ADF', '.Adf']:
        title = title.replace(ext_list, '')

    if title.find('(') > -1 and title.rfind(')') > -1:
        title_detail = title[title.rfind('('):title.rfind(')') + 1]
        title_detail = title_detail.replace('(', '').replace(')', '').strip().lower()
        if title_detail.find('disk') > -1 and title_detail.find('of'):
            title = title[:title.rfind('(')]

    if title.find(' ') == -1:
        if title.find('-') > -1:
            title = title.replace('-', ' ')
        elif title.find('_') > -1:
            title = title.replace('_', ' ')
        title = title.capitalize()

    return title


def get_rom_title(game):
    return game.get('title')


def parse_generic_zip_games(rom_path):
    rom_list = listdir(rom_path)
    game_list = []

    for i in tqdm(range(len(rom_list))):
        rom_filename = rom_list[i]
        if not is_excluded(rom_filename):
            title = rom_filename
            for ext_list in ['.zip', '.ZIP', '.Zip']:
                title = title.replace(ext_list, '')
            game_list.append({'title': title, 'filename': [rom_filename]})

    game_list.sort(key=get_rom_title)
    return game_list


def parse_amiga_games():
    print("Building Amiga Game List")
    rom_path = path.join(getcwd(), pardir, 'roms/amiga/')

    temp_rom_list = listdir(rom_path)
    rom_list = [] 

    for temp_filename in temp_rom_list:
        if not is_excluded(temp_filename):
            rom_list.append(temp_filename)

    rom_list.sort()
    d = levenshtein_distance(rom_list[0], rom_list[1])
    game_list = []

    # look for a
    rom_list.append('***end***')
    rom_idx = 0
    while rom_idx < len(rom_list):
        game_list.append({'title': beautify_filename(rom_list[rom_idx]), 'filename': [rom_list[rom_idx]]})
        for other_rom_idx in range(rom_idx + 1, len(rom_list)):
            a = rom_list[rom_idx]
            b = rom_list[other_rom_idx]
            if levenshtein_distance(rom_list[rom_idx], rom_list[other_rom_idx]) > 2:
                if other_rom_idx - rom_idx > 1:
                    for i in range(rom_idx + 1 , other_rom_idx):
                        game_list[-1]['filename'].append(rom_list[i])
                rom_idx = other_rom_idx - 1
                break
        rom_idx += 1

    game_list = game_list[:-1]
    # print(game_list)

    return game_list


def parse_apple_2_games():
    print("Building Apple // Game List")
    rom_path = path.join(getcwd(), pardir, 'roms/apple_2/')
    return parse_generic_zip_games(rom_path)


def parse_trs_80_games():
    print("Building TANDY TRS 80 Game List")
    rom_path = path.join(getcwd(), pardir, 'roms/tandy_trs_80/')
    return parse_generic_zip_games(rom_path)


def parse_amstrad_cpc_games():
    print("Building AMSTRAD CPC Game List")
    rom_path = path.join(getcwd(), pardir, 'roms/amstrad_cpc/')
    return parse_generic_zip_games(rom_path)


def parse_sega_megadrive_games():
    print("Building SEGA MEGADRIVE Game List")
    rom_path = path.join(getcwd(), pardir, 'roms/sega_megadrive/')
    return parse_generic_zip_games(rom_path)


def parse_mame_games():
    with open('mame.xml') as f:
        mame_list = parse(f.read())

    rom_path = path.join(getcwd(), pardir, 'roms/mame/')
    rom_list = listdir(rom_path)
    game_list = []

    print("Building MAME Game List")

    # list rom files
    for rom_idx in tqdm(range(len(rom_list))):
        rom_filename = rom_list[rom_idx]
        if not is_excluded(rom_filename):
            rom_name = rom_filename.replace('.zip', '')
            # iterate on all entries of mame.xml
            for key, value in mame_list.items():
                # iterate on all games among these entries
                for idx, ex in enumerate(mame_list[key]['game']):
                    # look the rom name
                    if str(ex['@name']) == rom_name:
                        # find the rom description (title)
                        title = str(ex['description'])
                        game_list.append({'title': title, 'filename': [rom_filename]})

    game_list.sort(key=get_rom_title)
    return game_list