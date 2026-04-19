import shutil
import subprocess
from pathlib import Path
from zipfile import BadZipFile, ZipFile

try:
    from .paths import PATHS
except ImportError:
    from paths import PATHS


def _paths(paths):
    return paths or PATHS


def _filenames(disk_filename):
    if disk_filename is None:
        return []
    if isinstance(disk_filename, (str, Path)):
        return [str(disk_filename)]
    return [str(filename) for filename in disk_filename]


def _stringify_command(command):
    return [str(arg) for arg in command]


def _missing_paths(required_paths):
    return [Path(required_path) for required_path in required_paths if not Path(required_path).exists()]


def _start_process(label, command, required_paths, paths, cwd=None):
    missing = _missing_paths(required_paths)
    if missing:
        print(f"Cannot start {label}; missing required file(s):")
        for missing_path in missing:
            print(f"  - {missing_path}")
        return None

    command = _stringify_command(command)
    print(command)
    try:
        return subprocess.Popen(command, cwd=str(cwd or paths.repo_root))
    except OSError as exc:
        print(f"Cannot start {label}: {exc}")
        return None


def temp_folder_path(paths=None):
    return _paths(paths).temp


def init_temp_folder(paths=None):
    temp_path = temp_folder_path(paths)
    if temp_path.exists():
        shutil.rmtree(temp_path)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


def build_amiga_command(disk_filename, paths=None):
    paths = _paths(paths)
    filenames = _filenames(disk_filename)
    winuae = paths.emulator_folder("winuae")
    amiga_rom_file = winuae / "roms" / "Kickstart 1.3.rom"

    disk_list = []
    for disk_idx, filename in enumerate(filenames[:4]):
        disk_list.append(f"-{disk_idx}")
        disk_list.append(paths.rom_folder("amiga") / filename)

    command = [winuae / "winuae64.exe", "-G", "-r", amiga_rom_file]
    command += ["-s", "gfx_fullscreen_amiga=true"]
    command += ["-s", "chipset=ecs_agnus"]
    command += ["-s", "chipmem_size=2"]
    command += ["-s", "bogomem_size=4"]
    command += ["-s", "cpu_speed=real"]
    command += ["-s", "cpu_multiplier=4"]
    command += ["-s", "cpu_cycle_exact=true"]
    command += ["-s", "cpu_memory_cycle_exact=true"]
    command += ["-s", "blitter_cycle_exact=true"]
    command += ["-s", "cycle_exact=true"]
    command += disk_list
    return command


def start_amiga(disk_filename, paths=None):
    paths = _paths(paths)
    filenames = _filenames(disk_filename)
    if not filenames:
        print("Cannot start Amiga; no disk was selected.")
        return None

    command = build_amiga_command(filenames, paths)
    required_paths = [
        paths.emulator_folder("winuae") / "winuae64.exe",
        paths.emulator_folder("winuae") / "roms" / "Kickstart 1.3.rom",
    ]
    required_paths += [paths.rom_folder("amiga") / filename for filename in filenames[:4]]
    return _start_process("Amiga", command, required_paths, paths)


def build_mame_command(disk_filename, paths=None):
    paths = _paths(paths)
    filenames = _filenames(disk_filename)
    selected_file = filenames[0] if filenames else ""
    return [
        paths.emulator_folder("mame") / "mame.exe",
        "-rompath",
        paths.rom_folder("mame"),
        paths.rom_folder("mame") / selected_file,
    ]


def start_mame(disk_filename, paths=None):
    paths = _paths(paths)
    filenames = _filenames(disk_filename)
    if not filenames:
        print("Cannot start MAME; no ROM was selected.")
        return None

    command = build_mame_command(filenames, paths)
    required_paths = [
        paths.emulator_folder("mame") / "mame.exe",
        paths.rom_folder("mame") / filenames[0],
    ]
    return _start_process("MAME", command, required_paths, paths)


def file_get_score(file):
    return file.get("score")


def build_amstrad_cpc_command(disk_filename, paths=None, autocmd=None, config_path=None, media_path=None):
    paths = _paths(paths)
    filenames = _filenames(disk_filename)
    selected_file = filenames[0] if filenames else ""
    caprice = paths.emulator_folder("caprice")
    config_path = config_path or caprice / "cap32.cfg"
    media_path = media_path or paths.rom_folder("amstrad_cpc") / selected_file

    command = [
        caprice / "cap32.exe",
        f"--cfg_file={config_path}",
    ]
    if autocmd is not None:
        command += ["--autocmd", autocmd]
    command.append(media_path)
    return command


def _extract_zip_member(zip_ref, member_name, destination_folder):
    destination_folder.mkdir(parents=True, exist_ok=True)
    extracted_path = destination_folder / Path(member_name).name
    with zip_ref.open(member_name) as source, extracted_path.open("wb") as target:
        shutil.copyfileobj(source, target)
    return extracted_path


def _prepare_amstrad_media(media_path, paths):
    suffix = media_path.suffix.lower()
    if suffix == ".dsk":
        return media_path, media_path
    if suffix == ".cpr":
        return media_path, None
    if suffix != ".zip":
        print(f"Cannot start Amstrad CPC; unsupported media type: {media_path.suffix}")
        return None, None

    try:
        with ZipFile(media_path, "r") as zip_ref:
            dsk_members = [member for member in zip_ref.namelist() if member.lower().endswith(".dsk") and not member.endswith("/")]
            if not dsk_members:
                print(f"Cannot start Amstrad CPC; ZIP archive does not contain a .dsk file: {media_path}")
                return None, None
            extracted_dsk = _extract_zip_member(zip_ref, dsk_members[0], init_temp_folder(paths))
            return media_path, extracted_dsk
    except BadZipFile:
        print(f"Cannot start Amstrad CPC; invalid ZIP archive: {media_path}")
        return None, None


def _run_catalog_command(command, paths):
    try:
        process = subprocess.Popen(_stringify_command(command), cwd=str(paths.repo_root), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, error = process.communicate()
    except OSError as exc:
        print(f"Catalog command failed to start: {exc}")
        return []

    if process.returncode != 0:
        details = error.decode(errors="replace").strip()
        if details:
            print(f"Catalog command failed: {details}")
        return []

    return result.decode(errors="replace").replace("\r", "").split("\n")


def _parse_cpcxfs_catalog(lines):
    disk_files = []
    grab = False
    for line in lines:
        if grab:
            grab_row = line.strip()
            if len(grab_row) > 0 and "|" in grab_row and "Bytes" not in grab_row:
                columns = list(map(str.strip, grab_row.split("|")))
                for column in columns:
                    start = column.find(" ") + 1
                    value = column[start:]
                    end = value.find(" ")
                    if end > 0:
                        disk_files.append({"filename": value[:end], "score": 0})
        elif line.strip().find("---------------------------------------") > -1:
            grab = True
    return disk_files


def _parse_samdisk_catalog(lines):
    disk_files = []
    for line in lines:
        grab_row = line.strip()
        if len(grab_row) > 0 and not grab_row.endswith("free"):
            grab_row = grab_row.split(".")
            filename = grab_row[0].strip()
            if filename.isalnum():
                if len(grab_row) > 1:
                    filename += "." + grab_row[1].split(" ")[0]
                disk_files.append({"filename": filename, "score": 0})
    return disk_files


def _valid_amstrad_dir_text(value):
    return all(char == 32 or 48 <= char <= 57 or 65 <= char <= 90 or char in (35, 36, 38, 39, 45, 64, 94, 95) for char in value)


def _parse_amstrad_directory_entries(data):
    disk_files = []
    seen = set()
    for offset in range(0, len(data) - 31, 32):
        entry = data[offset:offset + 32]
        user = entry[0]
        if user >= 16:
            continue

        name_bytes = bytes(char & 0x7f for char in entry[1:9])
        extension_bytes = bytes(char & 0x7f for char in entry[9:12])
        if not _valid_amstrad_dir_text(name_bytes) or not _valid_amstrad_dir_text(extension_bytes):
            continue

        name = name_bytes.decode("ascii", errors="ignore").strip()
        extension = extension_bytes.decode("ascii", errors="ignore").strip()
        record_count = entry[15]
        blocks = [block for block in entry[16:32] if block not in (0, 0xE5)]

        if not name or (record_count == 0 and not blocks):
            continue

        filename = f"{name}.{extension}" if extension else f"{name}."
        if filename not in seen:
            seen.add(filename)
            disk_files.append({"filename": filename, "score": 0})
    return disk_files


def _amstrad_dsk_track_chunks(dsk_file, max_tracks=8):
    try:
        data = Path(dsk_file).read_bytes()
    except OSError as exc:
        print(f"Cannot inspect Amstrad CPC disk image: {exc}")
        return []

    chunks = []
    if data.startswith(b"EXTENDED CPC DSK File"):
        track_count = data[0x30]
        side_count = max(data[0x31], 1)
        track_sizes = data[0x34:0x34 + (track_count * side_count)]
        offset = 0x100
        for track_idx, track_size_blocks in enumerate(track_sizes):
            track_size = track_size_blocks * 0x100
            if track_size <= 0:
                continue
            if track_idx >= max_tracks:
                break
            chunk = data[offset:offset + track_size]
            if chunk:
                chunks.append(chunk)
            offset += track_size
        return chunks

    if data.startswith(b"MV - CPCEMU Disk-File"):
        track_count = data[0x30]
        side_count = max(data[0x31], 1)
        track_size = int.from_bytes(data[0x32:0x34], "little")
        offset = 0x100
        for _ in range(min(track_count * side_count, max_tracks)):
            chunk = data[offset:offset + track_size]
            if chunk:
                chunks.append(chunk)
            offset += track_size
    return chunks


def _scan_amstrad_disk_directory(dsk_file):
    disk_files = []
    seen = set()
    for chunk in _amstrad_dsk_track_chunks(dsk_file):
        sector_data = chunk[0x100:]
        for disk_file in _parse_amstrad_directory_entries(sector_data):
            if disk_file["filename"] not in seen:
                seen.add(disk_file["filename"])
                disk_files.append(disk_file)
    return disk_files


def _inspect_amstrad_disk(dsk_file, paths):
    caprice = paths.emulator_folder("caprice")
    cpcxfs = caprice / "tools" / "cpcxfs" / "cpcxfsw.exe"
    samdisk = caprice / "tools" / "samdisk" / "SAMdisk.exe"

    disk_files = []
    if cpcxfs.exists():
        disk_files = _parse_cpcxfs_catalog(_run_catalog_command([cpcxfs, dsk_file, "-d"], paths))
    else:
        print(f"Amstrad CPC catalog tool is missing: {cpcxfs}")

    if len(disk_files) == 0:
        if samdisk.exists():
            disk_files = _parse_samdisk_catalog(_run_catalog_command([samdisk, "list", dsk_file], paths))
        else:
            print(f"Amstrad CPC fallback catalog tool is missing: {samdisk}")

    if len(disk_files) == 0:
        disk_files = _scan_amstrad_disk_directory(dsk_file)

    return disk_files


def _score_amstrad_disk_files(disk_files, selected_filename):
    for i, file in enumerate(disk_files):
        filename = file["filename"]
        if len(filename) <= 1:
            disk_files[i]["score"] -= 1
        if filename.find(".BIN") > -1:
            disk_files[i]["score"] -= 1
        if filename.find(".BAS") > -1:
            disk_files[i]["score"] += 1
        if filename.endswith("."):
            disk_files[i]["score"] += 1
        if len(filename) > 1 and selected_filename.lower().find(filename.split(".")[0].lower().replace(" ", "")) > -1:
            disk_files[i]["score"] += 1

    disk_files.sort(key=file_get_score, reverse=True)
    return disk_files


def _amstrad_autocmd_from_disk(dsk_file, selected_filename, paths):
    disk_files = _inspect_amstrad_disk(dsk_file, paths)
    disk_files = _score_amstrad_disk_files(disk_files, selected_filename)
    print(disk_files)

    if len(disk_files) > 0 and disk_files[0]["score"] >= 0:
        return 'run"' + disk_files[0]["filename"].split(".")[0].strip(" ")
    return "|cpm"


def start_amstrad_cpc(disk_filename, paths=None):
    paths = _paths(paths)
    filenames = _filenames(disk_filename)
    if not filenames:
        print("Cannot start Amstrad CPC; no disk or cartridge was selected.")
        return None

    selected_filename = filenames[0]
    media_path = paths.rom_folder("amstrad_cpc") / selected_filename
    if not media_path.exists():
        print(f"Cannot start Amstrad CPC; media file is missing: {media_path}")
        return None

    source_media, dsk_file = _prepare_amstrad_media(media_path, paths)
    if source_media is None:
        return None

    caprice = paths.emulator_folder("caprice")
    caprice_exe = caprice / "cap32.exe"

    if dsk_file is None:
        config_path = caprice / "cap32_6128plus.cfg"
        command = build_amstrad_cpc_command(filenames, paths, config_path=config_path, media_path=source_media)
        required_paths = [caprice_exe, config_path, source_media]
        return _start_process("Amstrad CPC", command, required_paths, paths, cwd=caprice)

    config_path = caprice / "cap32.cfg"
    launcher_cmd = _amstrad_autocmd_from_disk(dsk_file, selected_filename, paths)
    command = build_amstrad_cpc_command(filenames, paths, autocmd=launcher_cmd, config_path=config_path, media_path=source_media)
    required_paths = [caprice_exe, config_path, source_media]
    return _start_process("Amstrad CPC", command, required_paths, paths, cwd=caprice)
