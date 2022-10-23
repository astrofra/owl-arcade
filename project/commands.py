from os import getcwd, path, pardir, makedirs, listdir
import subprocess
from shutil import rmtree, move
from zipfile import ZipFile


print('getcwd:' + getcwd())


def temp_folder_path():
    # the temp folder is one level above the CWD ('dirname()')
    return path.join(path.dirname(getcwd()), '_temp')


def init_temp_folder():
    try:
        rmtree(temp_folder_path())
    except:
        print("no temp folder, will create one")
    makedirs(temp_folder_path(), exist_ok=True)


def start_amiga(disk_filename):
    amiga_rom_file = path.join(path.dirname(getcwd()), 'bin/emulators/winuae/roms', 'Kickstart 1.3.rom').replace('/', '\\')

    disk_list = []
    disk_idx = 0
    while disk_idx < 4 and disk_idx < len(disk_filename):
        disk_list.append('-' + str(disk_idx))
        disk_list.append(path.join(path.dirname(getcwd()), 'roms/amiga', disk_filename[disk_idx]))
        disk_idx += 1

    popen_cmd = ["../bin/emulators/winuae/winuae64.exe", '-G']
    popen_cmd += ['-r', amiga_rom_file]
    popen_cmd += ["-s", "gfx_fullscreen_amiga=true"]
    popen_cmd += ["-s", "chipset=ecs_agnus"]
    popen_cmd += ["-s", "chipmem_size=2"]
    popen_cmd += ["-s", "bogomem_size=4"]
    popen_cmd += ["-s", "cpu_speed=real"]
    popen_cmd += ["-s", "cpu_multiplier=4"]
    popen_cmd += ["-s", "cpu_cycle_exact=true"]
    popen_cmd += ["-s", "cpu_memory_cycle_exact=true"]
    popen_cmd += ["-s", "blitter_cycle_exact=true"]
    popen_cmd += ["-s", "cycle_exact=true"]
    popen_cmd += disk_list
    print(popen_cmd)
    return subprocess.Popen(popen_cmd)


def start_mame(disk_filename):
    popen_cmd = ["../bin/emulators/mame/mame.exe", '-rompath']
    popen_cmd.append(path.join(path.dirname(getcwd()), 'roms\\mame').replace('\\', '/'))
    popen_cmd.append(path.join('../roms/mame', disk_filename[0]).replace('\\', '/'))
    # .\bin\emulators\mame\mame.exe -rompath W:\dev\owl - arcade\roms\mame .\roms\mame\99lstwara.zip
    print(popen_cmd)
    return subprocess.Popen(popen_cmd)


def file_get_score(file):
    return file.get('score')


def start_amstrad_cpc(disk_filename):
    # WinApe.exe "W:\dev\owl-arcade\roms\amstrad_cpc\3D Fight (1985)(Loriciels)(fr).dsk" /A:3dfight
    # cpcxfsw.exe game -d
    # ..\bin\emulators\caprice\cap32.exe --cfg_file=../bin/emulators/caprice/cap32.cfg --autocmd run\"3dfight "W:\dev\owl-arcade\roms\amstrad_cpc\3D Fight (1985)(Loriciels)(fr).zip"
    init_temp_folder()

    game_filename = path.join(path.dirname(getcwd()), 'roms/amstrad_cpc', disk_filename[0]).replace('\\', '/')
    print("game_filename = " + game_filename)

    # extract the .dsk from a zip, if needed
    with ZipFile(game_filename, 'r') as zip_ref:
        zip_ref.extractall(temp_folder_path())

    # get the .dsk file
    dsk_file = None
    for file in listdir(temp_folder_path()):
        if file.lower().find('.dsk') > -1:
            dsk_file = file
            break

    if dsk_file is not None:
        print("dsk_file = " + dsk_file)

        dsk_file = path.join(temp_folder_path(), dsk_file).replace('\\', '/')
        safe_dsk_file = path.join(temp_folder_path(), 'cpcgame.dsk')
        move(dsk_file, safe_dsk_file)
        print("safe_dsk_file = " + safe_dsk_file)

        # extract the file catalog from the disk
        popen_cmd = ["..\\bin\\emulators\\caprice\\tools\\cpcxfs\\cpcxfsw.exe", safe_dsk_file, '-d']
        print(popen_cmd)
        p = subprocess.Popen(popen_cmd, stdout=subprocess.PIPE)
        result, err = p.communicate()
        result = result.decode().split('\n')
    #    print(result)

        disk_files = []

        grab = False
        for line in result:
            if grab:
                grab_row = line.strip()
                if len(grab_row) > 0 and grab_row.find('|') and grab_row.find('Bytes') == -1:
                    grab_row = grab_row.split('|')
                    grab_row = list(map(str.strip, grab_row))
                    for i, r in enumerate(grab_row):
                        cs = r.find(' ') + 1
                        r = r[cs:]
                        cs = r.find(' ')
                        disk_files.append({'filename': r[:cs], 'score': 0})
            elif line.strip().find('---------------------------------------') > -1:
                grab = True

        # FALLBACK, extract the file catalog from the disk
        if len(disk_files) == 0:
            popen_cmd = ["..\\bin\\emulators\\caprice\\tools\\samdisk\\samdisk.exe", 'list', safe_dsk_file]
            print(popen_cmd)
            p = subprocess.Popen(popen_cmd, stdout=subprocess.PIPE)
            result, err = p.communicate()
            result = result.decode().replace('\r', '').split('\n')
            result = list(map(str.strip, result))

            # print(result)

            for line in result:
                grab_row = line.strip()
                if len(grab_row) > 0 and not grab_row.endswith('free'):
                    grab_row = grab_row.split('.')
                    filename = grab_row[0].strip()
                    if filename.isalnum():
                        if len(grab_row) > 1:
                            filename += '.' + grab_row[1].split(' ')[0]
                        print(filename)
                        disk_files.append({'filename': filename, 'score': 0})

        for i, file in enumerate(disk_files):
            if len(file['filename']) <= 1:  # Too short bo be useful
                disk_files[i]['score'] -= 1
            if file['filename'].find('.BIN') > -1:  # thumb down .BIN files
                disk_files[i]['score'] -= 1
            if file['filename'].find('.BAS') > -1:  # thumb down .BIN files
                disk_files[i]['score'] += 1
            if file['filename'].endswith('.'):  # thumb up files with no extension
                disk_files[i]['score'] += 1
            if len(file['filename']) > 1 and disk_filename[0].lower().find(file['filename'].split('.')[0].lower().replace(' ', '')) > -1:  # if the filename matches the disk name
                disk_files[i]['score'] += 1

        disk_files.sort(key=file_get_score, reverse=True)

        print(disk_files)

        if len(disk_files) > 0:
            # find the most likely file to be used as a command line
            launcher_cmd = 'run\"' + disk_files[0]['filename'].split('.')[0].strip(' ')
        else:
            # if none, it might be a CPM disk
            launcher_cmd = '|cpm'

        # CPC 6128 configuration
        popen_cmd = ["..\\bin\\emulators\\caprice\\cap32.exe", "--cfg_file=../bin/emulators/caprice/cap32.cfg",
                     "--autocmd", launcher_cmd]

    else:
        # 6128 Plus configuration
        print("CPR found! Starting a Amstrad Plus model!")
        popen_cmd = ["..\\bin\\emulators\\caprice\\cap32.exe", "--cfg_file=../bin/emulators/caprice/cap32_6128plus.cfg"]

    # Append the filename (disk, rom...) to the command line
    popen_cmd.append(path.join('../roms/amstrad_cpc', disk_filename[0]).replace('\\', '/'))

    print(popen_cmd)

    return subprocess.Popen(popen_cmd)
