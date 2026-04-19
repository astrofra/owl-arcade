import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from project import commands, platforms, rom_parser
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

    def test_amstrad_launcher_runs_caprice_from_emulator_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")
            caprice = paths.emulator_folder("caprice")
            rom_folder = paths.rom_folder("amstrad_cpc")
            caprice.mkdir(parents=True)
            rom_folder.mkdir(parents=True)
            (caprice / "cap32.exe").write_text("")
            (caprice / "cap32.cfg").write_text("")
            (rom_folder / "demo.dsk").write_text("")

            expected_process = object()
            with patch("project.commands.subprocess.Popen", return_value=expected_process) as popen:
                process = commands.start_amstrad_cpc(["demo.dsk"], paths)

            self.assertIs(process, expected_process)
            self.assertEqual(popen.call_args.kwargs["cwd"], str(caprice))

    def test_machine_catalog_is_sorted_and_uses_production_slots(self):
        machines = platforms.build_machine_catalog()
        names = [machine["name"] for machine in machines]

        self.assertEqual(names, sorted(names))
        self.assertTrue(all("productions" in machine for machine in machines))
        self.assertFalse(any("games" in machine for machine in machines))
        amstrad = next(machine for machine in machines if machine["name"] == "Amstrad CPC 464")
        self.assertEqual(amstrad["scene_path"], "amstrad_cpc_464.scn")
        self.assertEqual(amstrad["rom_folder"], "amstrad_cpc")
        self.assertIs(amstrad["launcher"], commands.start_amstrad_cpc)

    def test_load_machine_productions_passes_project_paths_to_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")
            seen_paths = []

            def parser(parser_paths):
                seen_paths.append(parser_paths)
                return [{"title": "Demo", "filename": ["demo.zip"]}]

            machines = platforms.build_machine_catalog([
                platforms.MachineDefinition("Demo Machine", rom_folder="demo", parser=parser),
            ])

            platforms.load_machine_productions(machines, paths)

            self.assertEqual(seen_paths, [paths])
            self.assertEqual(machines[0]["productions"], [{"title": "Demo", "filename": ["demo.zip"]}])

    def test_visible_production_entries_does_not_duplicate_short_lists(self):
        productions = [{"title": "Gryzor", "filename": ["Gryzor.dsk"]}]

        self.assertEqual(platforms.visible_production_entries(productions, 0, limit=10), productions)

    def test_visible_production_entries_wraps_only_when_list_exceeds_limit(self):
        productions = [{"title": f"Demo {idx}", "filename": [f"demo{idx}.zip"]} for idx in range(12)]
        visible = platforms.visible_production_entries(productions, 10, limit=5)

        self.assertEqual([entry["title"] for entry in visible], ["Demo 10", "Demo 11", "Demo 0", "Demo 1", "Demo 2"])

    def test_amstrad_autocmd_falls_back_to_cpm_for_bin_only_disks(self):
        with patch("project.commands._inspect_amstrad_disk", return_value=[{"filename": "DISC.BIN", "score": 0}]):
            autocmd = commands._amstrad_autocmd_from_disk(Path("demo.dsk"), "Gryzor (CPM).dsk", object())

        self.assertEqual(autocmd, "|cpm")

    def test_amstrad_autocmd_prefers_basic_loader(self):
        with patch("project.commands._inspect_amstrad_disk", return_value=[{"filename": "DEMO.BAS", "score": 0}]):
            autocmd = commands._amstrad_autocmd_from_disk(Path("demo.dsk"), "Demo.dsk", object())

        self.assertEqual(autocmd, 'run"DEMO')


if __name__ == "__main__":
    unittest.main()
