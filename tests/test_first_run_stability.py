import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from project import commands, platforms, pouet_library, rom_parser
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

    def test_parser_ignores_pouet_storage_folder_and_loads_manifest_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")
            rom_folder = paths.rom_folder("amstrad_cpc")
            media_folder = rom_folder / "_pouet" / "123-demo" / "media"
            media_folder.mkdir(parents=True)
            (media_folder / "demo.dsk").write_text("")
            paths.db.mkdir(parents=True)
            with (paths.db / "pouet-library.json").open("w") as manifest_file:
                json.dump(
                    {
                        "platforms": {
                            "amstrad_cpc": [
                                {
                                    "title": "Pouet Demo",
                                    "filename": ["_pouet/123-demo/media/demo.dsk"],
                                    "launchable": True,
                                }
                            ]
                        }
                    },
                    manifest_file,
                )

            entries = rom_parser.parse_amstrad_cpc_games(paths)

            self.assertEqual(entries, [{"title": "Pouet Demo", "filename": ["_pouet/123-demo/media/demo.dsk"], "launchable": True}])

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

    def test_pouet_top_selection_uses_rank_and_platform(self):
        prods = [
            {"id": "1", "name": "Other", "rank": "1", "download": "https://example.invalid/other.zip", "platforms": {"1": {"name": "PC"}}},
            {"id": "2", "name": "Second", "rank": "20", "download": "https://example.invalid/second.zip", "platforms": {"2": {"name": "Amstrad CPC"}}},
            {"id": "3", "name": "First", "rank": "10", "download": "https://example.invalid/first.zip", "platforms": {"2": {"name": "Amstrad CPC"}}},
            {"id": "4", "name": "No Download", "rank": "2", "platforms": {"2": {"name": "Amstrad CPC"}}},
        ]

        selected = pouet_library.select_top_prods(prods, ["Amstrad CPC"], limit=2)

        self.assertEqual([prod["id"] for prod in selected], ["3", "2"])

    def test_pouet_download_urls_are_normalized_for_storage(self):
        self.assertEqual(
            pouet_library.normalize_download_url("https://files.scene.org/view/parties/demo.zip"),
            "https://files.scene.org/get/parties/demo.zip",
        )
        self.assertEqual(
            pouet_library.filename_from_url("http://example.invalid/fetch.php?media=tmp:demo.zip", "fallback.bin"),
            "demo.zip",
        )

    def test_pouet_zip_media_is_extracted_to_launchable_manifest_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "repo")
            config = pouet_library.PLATFORM_CONFIGS["amstrad_cpc"]
            prod = {
                "id": "123",
                "name": "Demo",
                "rank": "1",
                "download": "https://example.invalid/demo.zip",
                "platforms": {"1": {"name": "Amstrad CPC"}},
                "groups": [{"name": "Group"}],
            }
            prod_folder = pouet_library.platform_storage_folder(paths, config, prod)
            archive_path = prod_folder / "demo.zip"
            archive_path.parent.mkdir(parents=True)
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("disk/Demo disk 1 side B.dsk", b"side b")
                archive.writestr("disk/Demo disk 1 side A.dsk", b"side a")

            entry = pouet_library.build_manifest_entry(prod, config, paths)
            launch_info = pouet_library.prepare_launch_media(paths, config, archive_path)
            entry["launchable"] = launch_info["launchable"]
            entry["launch"]["status"] = launch_info["status"]
            entry["launch"]["media"] = pouet_library.relative_to_rom_folder(paths, config, launch_info["media_path"])
            entry["filename"] = [entry["launch"]["media"]]

            self.assertTrue(entry["launchable"])
            self.assertEqual(entry["filename"], ["_pouet/123-demo/media/Demo disk 1 side A.dsk"])
            self.assertTrue((paths.rom_folder("amstrad_cpc") / entry["filename"][0]).exists())

    def test_amstrad_autocmd_falls_back_to_cpm_for_bin_only_disks(self):
        with patch("project.commands._inspect_amstrad_disk", return_value=[{"filename": "DISC.BIN", "score": 0}]):
            autocmd = commands._amstrad_autocmd_from_disk(Path("demo.dsk"), "Gryzor (CPM).dsk", object())

        self.assertEqual(autocmd, "|cpm")

    def test_amstrad_autocmd_prefers_basic_loader(self):
        with patch("project.commands._inspect_amstrad_disk", return_value=[{"filename": "DEMO.BAS", "score": 0}]):
            autocmd = commands._amstrad_autocmd_from_disk(Path("demo.dsk"), "Demo.dsk", object())

        self.assertEqual(autocmd, 'run"DEMO')

    def test_amstrad_raw_directory_scan_finds_extensionless_loader(self):
        directory = bytearray([0xE5] * 512)
        directory[0:32] = b"\x00PHX        \x00\x00\x00\x10\x02\x03" + (b"\x00" * 14)

        self.assertEqual(commands._parse_amstrad_directory_entries(directory), [{"filename": "PHX.", "score": 0}])

    def test_amstrad_autocmd_uses_raw_directory_when_catalog_tools_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsk_path = Path(tmp) / "phX.dsk"
            header = bytearray(256)
            header[: len(b"EXTENDED CPC DSK File\r\nDisk-Info\r\n")] = b"EXTENDED CPC DSK File\r\nDisk-Info\r\n"
            header[0x30] = 1
            header[0x31] = 1
            header[0x34] = 3

            track = bytearray(0x300)
            track[: len(b"Track-Info\r\n")] = b"Track-Info\r\n"
            track[0x100:0x120] = b"\x00PHX        \x00\x00\x00\x10\x02\x03" + (b"\x00" * 14)
            dsk_path.write_bytes(header + track)

            with patch("project.commands._run_catalog_command", return_value=[]):
                autocmd = commands._amstrad_autocmd_from_disk(dsk_path, "phX.dsk", ProjectPaths(Path(tmp)))

        self.assertEqual(autocmd, 'run"PHX')


if __name__ == "__main__":
    unittest.main()
