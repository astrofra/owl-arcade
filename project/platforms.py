from dataclasses import dataclass
from typing import Callable, Optional

try:
    from .commands import start_amiga, start_amstrad_cpc, start_mame
    from .paths import PATHS
    from .rom_parser import (
        parse_amiga_games,
        parse_amstrad_cpc_games,
        parse_apple_2_games,
        parse_mame_games,
        parse_trs_80_games,
    )
except ImportError:
    from commands import start_amiga, start_amstrad_cpc, start_mame
    from paths import PATHS
    from rom_parser import (
        parse_amiga_games,
        parse_amstrad_cpc_games,
        parse_apple_2_games,
        parse_mame_games,
        parse_trs_80_games,
    )


@dataclass(frozen=True)
class MachineDefinition:
    name: str
    pouet_name: Optional[str] = None
    scene_path: Optional[str] = None
    rom_folder: Optional[str] = None
    parser: Optional[Callable] = None
    launcher: Optional[Callable] = None

    def to_runtime_machine(self):
        return {
            "name": self.name,
            "pouet_name": self.pouet_name,
            "scene_path": self.scene_path,
            "path": self.scene_path,
            "rom_folder": self.rom_folder,
            "productions": [],
            "parser": self.parser,
            "launcher": self.launcher,
        }


MACHINE_DEFINITIONS = [
    MachineDefinition("Commodore 64", "Commodore 64", "commodore_64.scn"),
    MachineDefinition("Super Nintendo", "SNES/Super Famicom", "nintendo_snes.scn"),
    MachineDefinition("Apple //e", "Apple II", "apple_2_e.scn", "apple_2", parse_apple_2_games),
    MachineDefinition("Atari VCS 2600", "Atari VCS", "atari_vcs_2600.scn"),
    MachineDefinition(
        "Tandy TRS-80 III",
        "TRS-80/CoCo/Dragon",
        "tandy_trs_80.scn",
        "tandy_trs_80",
        parse_trs_80_games,
    ),
    MachineDefinition(
        "Amstrad CPC 464",
        "Amstrad CPC",
        "amstrad_cpc_464.scn",
        "amstrad_cpc",
        parse_amstrad_cpc_games,
        start_amstrad_cpc,
    ),
    MachineDefinition("Nec PC/FX", None, "nec_pcfx.scn"),
    MachineDefinition("Arcade", None, None, "mame", parse_mame_games, start_mame),
    MachineDefinition(
        "Commodore Amiga",
        "Amiga OCS/ECS",
        "commodore_amiga_500.scn",
        "amiga",
        parse_amiga_games,
        start_amiga,
    ),
]


def machine_get_name(machine):
    return machine.get("name")


def build_machine_catalog(definitions=None):
    if definitions is None:
        definitions = MACHINE_DEFINITIONS
    machines = [definition.to_runtime_machine() for definition in definitions]
    machines.sort(key=machine_get_name)
    return machines


def load_machine_productions(machines, paths=None):
    paths = paths or PATHS
    for machine in machines:
        parser = machine.get("parser")
        if parser is None:
            machine["productions"] = []
        else:
            machine["productions"] = parser(paths)
    return machines


def machine_productions(machine):
    return machine.get("productions", [])


def visible_production_entries(productions, idx, limit=10):
    visible_count = min(limit, len(productions))
    return [productions[(i + idx) % len(productions)] for i in range(visible_count)]
