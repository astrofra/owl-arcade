from dataclasses import dataclass
from pathlib import Path

try:
    from .paths import PATHS, ProjectPaths
except ImportError:
    from paths import PATHS, ProjectPaths


ERROR = "error"
WARNING = "warning"

REQUIRED_RENDER_ASSETS = [
    Path("background.scn"),
    Path("core") / "shader" / "font.fsb",
    Path("core") / "shader" / "font.vsb",
    Path("fonts") / "ROBOTO-THIN.TTF",
    Path("fonts") / "ROBOTO-MEDIUM.TTF",
]

IGNORED_CONTENT_FILES = {".gitkeep", ".git", ".gitignore"}


@dataclass(frozen=True)
class PreflightIssue:
    level: str
    code: str
    message: str
    path: Path = None


def _issue(level, code, message, path=None):
    return PreflightIssue(level=level, code=code, message=message, path=Path(path) if path else None)


def _has_user_content(folder):
    if not folder.exists():
        return False
    return any(child.name not in IGNORED_CONTENT_FILES for child in folder.iterdir())


def _launcher_names(machines):
    names = set()
    for machine in machines:
        launcher = machine.get("launcher")
        if launcher is not None:
            names.add(getattr(launcher, "__name__", str(launcher)))
    return names


def _warn_if_missing(issues, code, message, file_path):
    if not file_path.exists():
        issues.append(_issue(WARNING, code, message, file_path))


def run_preflight(paths=None, machines=None):
    paths = paths or PATHS
    machines = machines or []
    issues = []

    for asset in REQUIRED_RENDER_ASSETS:
        asset_path = paths.assets / asset
        if not asset_path.exists():
            issues.append(_issue(ERROR, "missing_render_asset", f"Required render asset is missing: {asset}", asset_path))

    rom_folders = sorted({machine.get("rom_folder") for machine in machines if machine.get("rom_folder")})
    for folder_name in rom_folders:
        rom_folder = paths.rom_folder(folder_name)
        if not rom_folder.exists():
            rom_folder.mkdir(parents=True, exist_ok=True)
            issues.append(_issue(WARNING, "created_rom_folder", f"ROM folder was missing and has been created: {folder_name}", rom_folder))
        if not _has_user_content(rom_folder):
            issues.append(_issue(WARNING, "empty_rom_folder", f"ROM folder has no launchable content: {folder_name}", rom_folder))

    for machine in machines:
        scene_path = machine.get("scene_path") or machine.get("path")
        if scene_path is not None:
            asset_path = paths.assets / "machines" / scene_path
            if not asset_path.exists():
                issues.append(_issue(WARNING, "missing_machine_scene", f"Machine scene asset is missing: {machine.get('name')}", asset_path))

    if not (paths.db / "prods.json").exists():
        issues.append(_issue(WARNING, "missing_optional_db", "Optional Pouet metadata cache is missing: db/prods.json", paths.db / "prods.json"))

    launcher_names = _launcher_names(machines)

    if "start_mame" in launcher_names:
        _warn_if_missing(issues, "missing_mame", "MAME executable is missing.", paths.emulator_folder("mame") / "mame.exe")
        _warn_if_missing(issues, "missing_mame_xml", "MAME metadata file is missing.", paths.mame_xml)

    if "start_amiga" in launcher_names:
        winuae = paths.emulator_folder("winuae")
        _warn_if_missing(issues, "missing_winuae", "WinUAE executable is missing.", winuae / "winuae64.exe")
        _warn_if_missing(issues, "missing_amiga_kickstart", "Amiga Kickstart ROM is missing.", winuae / "roms" / "Kickstart 1.3.rom")

    if "start_amstrad_cpc" in launcher_names:
        caprice = paths.emulator_folder("caprice")
        _warn_if_missing(issues, "missing_caprice", "Caprice32 executable is missing.", caprice / "cap32.exe")
        _warn_if_missing(issues, "missing_caprice_cfg", "Caprice32 CPC config is missing.", caprice / "cap32.cfg")
        _warn_if_missing(issues, "missing_caprice_plus_cfg", "Caprice32 Plus config is missing.", caprice / "cap32_6128plus.cfg")
        _warn_if_missing(issues, "missing_cpcxfs", "Caprice CPC catalog tool is missing.", caprice / "tools" / "cpcxfs" / "cpcxfsw.exe")
        _warn_if_missing(issues, "missing_samdisk", "SAMdisk fallback catalog tool is missing.", caprice / "tools" / "samdisk" / "SAMdisk.exe")

    return issues


def has_preflight_errors(issues):
    return any(issue.level == ERROR for issue in issues)


def print_preflight_report(issues):
    if not issues:
        print("[preflight] OK")
        return

    print("[preflight] Environment report")
    for level in (ERROR, WARNING):
        level_issues = [issue for issue in issues if issue.level == level]
        if not level_issues:
            continue
        print(f"[preflight] {level.upper()}S")
        for issue in level_issues:
            if issue.path is not None:
                print(f"  - {issue.message} ({issue.path})")
            else:
                print(f"  - {issue.message}")
