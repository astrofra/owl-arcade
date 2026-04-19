import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from project import commands, rom_parser
from project.paths import ProjectPaths
from project.preflight import ERROR, WARNING, run_preflight


class FirstRunStabilityTests(unittest.TestCase):
    def test_project_paths_are_repo_root_based(self):
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            elsewhere = Path(tmp) / "elsewhere"
            root.mkdir()
            elsewhere.mkdir()

            paths = ProjectPaths(root)
            os.chdir(elsewhere)
            try:
                self.assertEqual(paths.repo_root, root.resolve())
                self.assertEqual(paths.roms, root.resolve() / "roms")
                self.assertEqual(paths.bin, root.resolve() / "bin")
                self.assertEqual(paths.db, root.resolve() / "db")
                self.assertEqual(paths.assets, root.resolve() / "project" / "assets")
                self.assertEqual(paths.temp, root.resolve() / "_temp")
            finally:
                os.chdir(original_cwd)

    def test_parser_uses_repo_rom_folder_not_cwd(self):
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            elsewhere = Path(tmp) / "elsewhere"
            rom_folder = root / "roms" / "apple_2"
            rom_folder.mkdir(parents=True)
            elsewhere.mkdir()
            (rom_folder / "Demo.zip").write_text("")

            paths = ProjectPaths(root)
            os.chdir(elsewhere)
            try:
                games = rom_parser.parse_apple_2_games(paths)
                self.assertEqual(games, [{"title": "Demo", "filename": ["Demo.zip"]}])
                self.assertFalse((elsewhere / "roms").exists())
            finally:
                os.chdir(original_cwd)

    def test_command_builders_use_absolute_repo_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")

            commands_to_check = [
                commands.build_mame_command(["demo.zip"], paths),
                commands.build_amiga_command(["demo.adf"], paths),
                commands.build_amstrad_cpc_command(["demo.dsk"], paths, autocmd='run"demo'),
            ]

            for command in commands_to_check:
                path_like_args = [arg for arg in command if isinstance(arg, Path)]
                cfg_args = [str(arg).split("=", 1)[1] for arg in command if str(arg).startswith("--cfg_file=")]
                for arg in path_like_args + [Path(cfg_arg) for cfg_arg in cfg_args]:
                    self.assertTrue(Path(arg).is_absolute(), arg)
                    self.assertIn(str(paths.repo_root), str(arg))
                    self.assertNotIn("..", str(arg).replace("\\", "/").split("/"))

    def test_preflight_errors_for_assets_and_warns_for_optional_runtime_pieces(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")
            machines = [
                {"name": "Arcade", "path": None, "rom_folder": "mame", "launcher": commands.start_mame},
                {"name": "Amiga", "path": "commodore_amiga_500.scn", "rom_folder": "amiga", "launcher": commands.start_amiga},
                {"name": "Amstrad CPC", "path": "amstrad_cpc_464.scn", "rom_folder": "amstrad_cpc", "launcher": commands.start_amstrad_cpc},
            ]

            issues = run_preflight(paths, machines)
            levels = {issue.level for issue in issues}
            codes = {issue.code for issue in issues}

            self.assertIn(ERROR, levels)
            self.assertIn(WARNING, levels)
            self.assertIn("missing_render_asset", codes)
            self.assertIn("missing_mame", codes)
            self.assertIn("missing_winuae", codes)
            self.assertIn("missing_caprice", codes)
            self.assertTrue((paths.roms / "mame").exists())
            self.assertTrue((paths.roms / "amiga").exists())
            self.assertTrue((paths.roms / "amstrad_cpc").exists())

    def test_launcher_wrapper_returns_none_with_missing_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")
            rom_folder = paths.rom_folder("mame")
            rom_folder.mkdir(parents=True)
            (rom_folder / "demo.zip").write_text("")

            output = io.StringIO()
            with redirect_stdout(output):
                process = commands.start_mame(["demo.zip"], paths)

            self.assertIsNone(process)
            self.assertIn("Cannot start MAME", output.getvalue())
            self.assertIn("mame.exe", output.getvalue())


if __name__ == "__main__":
    unittest.main()
