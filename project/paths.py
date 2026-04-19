from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    repo_root: Path

    def __post_init__(self):
        object.__setattr__(self, "repo_root", self.repo_root.resolve())

    @property
    def project(self):
        return self.repo_root / "project"

    @property
    def roms(self):
        return self.repo_root / "roms"

    @property
    def bin(self):
        return self.repo_root / "bin"

    @property
    def db(self):
        return self.repo_root / "db"

    @property
    def resources(self):
        return self.project / "resources"

    @property
    def assets(self):
        return self.project / "assets"

    @property
    def temp(self):
        return self.repo_root / "_temp"

    @property
    def mame_xml(self):
        return self.project / "mame.xml"

    def rom_folder(self, platform_folder):
        return self.roms / platform_folder

    def emulator_folder(self, emulator_name):
        return self.bin / "emulators" / emulator_name


PATHS = ProjectPaths(Path(__file__).resolve().parents[1])
