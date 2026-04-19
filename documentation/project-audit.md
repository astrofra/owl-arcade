# Owl Arcade Project Audit

Date: 2026-04-19

## Scope

This audit reviews the current repository as a front-end for emulators intended to watch demoscene productions. It focuses on product direction, current implementation quality, urgent blockers, missing capabilities, and longer-term improvement paths.

The review is based on the repository structure, `README.md`, the Python source under `project/`, the batch entry points, the resource pipeline, and the current local working tree state. No runtime rendering test was performed, because launching the application would open a Harfang window and the repository has no automated test suite.

## General Philosophy, Goal, And Audience

Owl Arcade is not a generic ROM launcher. Its strongest idea is a "virtual museum" approach: a 3D space where historical machines are presented as objects, and where the user selects a machine and launches relevant productions from that context. This makes the project closer to a curated demoscene viewer than to a conventional emulator manager.

The stated goal is to make landmark games and demos browsable through a polished retro-computing front-end, with local Windows emulators, automatic ROM or disk parsing, and eventual bootstrap from public-domain demoscene productions listed on Pouet.

The natural audience is:

- demoscene spectators who want to watch productions without manually learning each emulator;
- event or exhibition setups needing a visual, kiosk-like way to browse retro machines;
- retro-computing enthusiasts who value the machine context, not only the executable file;
- curators or preservation-minded users who want metadata, platform grouping, and reproducible launch recipes.

At the current stage, the project is still more suitable for developers and technically comfortable retro users than for casual viewers. The repository contains a strong visual prototype and early launch plumbing, but setup, data ingestion, platform coverage, and failure handling are not yet end-user ready.

## Current Architecture Snapshot

- `project/main.py` is the application entry point. It initializes Harfang, loads the 3D scene, defines the static list of machines, parses ROM folders, handles keyboard navigation, and launches emulator processes.
- `project/rom_parser.py` builds per-platform lists from `roms/<platform>/` folders. Most parsers are simple filename-based scanners; MAME additionally reads `project/mame.xml`.
- `project/commands.py` contains emulator launch commands for Amiga, MAME, and Amstrad CPC. The Amstrad launcher has the most complete logic, including CPC disk catalog inspection.
- `project/fetch_pouet_prods.py` downloads the Pouet data dump and groups productions by platform, but this path is not wired into the main UI.
- `project/fetch_binaries.py` contains early automation for Harfang, embedded Python, and MAME downloads, but it is not part of the normal startup path.
- `project/resources/` contains source assets. `project/assets/` is the compiled Harfang asset output and is ignored by Git.
- The current local tree includes untracked emulator binaries under `bin/emulators/caprice/`, an untracked `db/prods.json`, and one untracked Amstrad CPC disk image.

## Strengths At The Current Stage

- The product concept is clear and distinctive. The 3D museum metaphor gives the front-end an identity that fits demoscene discovery better than a flat file list.
- The Harfang/BGFX asset pipeline is already present, with source resources, compiled assets, fonts, shaders, sound effects, and multiple machine scenes.
- The machine list in `main.py` already separates display name, Pouet platform name, 3D scene path, ROM parser, and launcher. This is a useful seed for a future platform abstraction.
- The project already models several historically relevant platforms: Commodore 64, SNES, Apple II, Atari VCS, TRS-80, Amstrad CPC, NEC PC-FX, Arcade, and Amiga.
- The Amstrad CPC path is more advanced than a simple file launch. It can inspect a disk catalog through Caprice tooling and attempts to infer the best `RUN` command.
- Pouet integration has started in a practical way by using Pouet's dump data rather than scraping pages.
- The repository contains GPLv3 licensing and visible asset/code credits in the README.
- ROM directories are separated by platform, which gives the project a simple and understandable content layout.

## Weaknesses At The Current Stage

- `main.py` is doing too much. Rendering, input, scene animation, machine definitions, ROM indexing, and process launching are all coupled in one file.
- The setup story is fragile. There are two requirements files with different contents, batch files are Windows-only, and the README does not describe a reliable first-run sequence.
- The root `requirements.txt` used by `0-requirements.bat` omits dependencies that the code imports, notably `requests` and `tqdm`.
- Path handling is inconsistent. Parsers use the current working directory as the repository root, while launchers in `commands.py` often use `path.dirname(getcwd())` and `../bin/...`, which points outside the repository when launched through `2-start_app.bat`.
- Most machines shown in the UI have no launcher and sometimes no parser. This can make the interface look broader than the actual playable/watchable platform support.
- Pouet metadata and local launchable artifacts are not connected. The project can build a grouped Pouet database, but the UI still lists local ROM filenames.
- The domain vocabulary still says "games" in code and UI functions. For a demoscene viewer, this will become limiting because productions need author/group, party, year, platform, rank, release type, license, and launch notes.
- Emulator availability is not validated at startup. Missing `mame.exe`, missing WinUAE, missing Kickstart ROMs, missing Caprice configs, or missing compiled assets will fail late or through raw exceptions.
- Third-party binary and ROM licensing is not documented enough. Local untracked emulator files and ROMs exist, but the repository does not clearly define what may be redistributed, what must be downloaded by the user, and what is only for local development.
- No automated tests, CI, linting, type checks, or smoke tests are present. Small parser or path regressions can easily break startup or launch behavior.

## Urgent Issues To Fix

1. Fix repository-root path resolution.

   Use a central root path based on `Path(__file__).resolve().parents[1]`, then derive `roms/`, `bin/`, `db/`, `project/resources/`, `project/assets/`, and temporary directories from it. This is the most urgent issue because the current launchers point outside the repository when the documented batch file is used.

2. Align dependency installation.

   Merge or reconcile `requirements.txt` and `project/requirements.txt`. The startup path imports modules that require `requests` and `tqdm`, but the root install file does not install them. Pin versions consistently, or use a single project-level dependency file.

3. Add startup validation and actionable errors.

   Before opening the main loop, check for compiled assets, required ROM directories, known emulator binaries, emulator configs, and optional metadata databases. Missing pieces should produce a clear message instead of a crash or a silent empty list.

4. Correct emulator launch path behavior.

   `commands.py` should use absolute paths built from the repository root, not `../bin/...` or `path.dirname(getcwd())`. This affects Amstrad CPC, MAME, Amiga, temporary extraction, and ROM file lookup.

5. Harden the Amstrad CPC launcher.

   The launcher should correctly distinguish `.dsk`, zipped `.dsk`, `.cpr`, and unsupported archives. It should also validate ZIP extraction paths, handle catalog-tool failures, and avoid assuming that a ZIP without a `.dsk` is automatically a Plus cartridge.

6. Remove UI freezes from emulator process handling.

   `process.wait()` is called inside the render loop after a launch. If the desired behavior is to pause the front-end while the emulator runs, make that state explicit. If not, process polling should be non-blocking.

7. Document binary and ROM licensing boundaries.

   The project needs a clear policy for bundled emulators, emulator BIOS/ROM files, user-provided content, public-domain demos, and generated caches. This matters especially for Amiga Kickstart ROMs and any platform BIOS files.

## Missing Features That Can Block Use

- A complete first-run bootstrap: install dependencies, compile assets, install or locate emulators, create folders, validate the environment, and start the UI.
- A supported content acquisition flow for demoscene productions. Pouet metadata alone is not enough; the project needs download URLs, license filtering, archive extraction, file selection, and launch recipes.
- Launchers for most visible machines. Commodore 64, SNES, Apple II, Atari VCS, TRS-80, and NEC PC-FX currently do not have usable launchers in the main machine table.
- A configuration system for emulator paths, ROM paths, fullscreen/windowed mode, resolution, input preferences, and cache locations.
- User-facing feedback for empty libraries, unsupported machines, missing emulator binaries, and launch failures.
- Controls documentation inside the UI or README. The current keyboard model is discoverable only by reading code.
- Search, filtering, and metadata browsing. A demoscene library quickly becomes unusable if it is only a flat filename list per machine.
- Per-production compatibility data. Many demos require exact machine models, memory, disk order, boot commands, joystick state, or emulator-specific options.
- Cross-platform implementation. Ubuntu support is marked WIP, but the current scripts and launch commands are Windows-focused.
- A reproducible test or smoke-test path that verifies parsers, asset availability, and launcher command construction without opening a full 3D window.

## Longer-Term Improvement Paths

- Introduce a small domain model: `Platform`, `Emulator`, `Production`, `Artifact`, `LaunchProfile`, and `MachineScene`. This would separate demoscene metadata from local files and emulator commands.
- Move each platform into its own adapter module with parser, metadata mapper, compatibility rules, and launcher command builder.
- Consider a manifest-driven library. A curated manifest can store Pouet IDs, titles, groups, years, party results, download sources, hashes, platform requirements, and tested launch profiles.
- Build a safe downloader/cache layer with hashes, source URLs, license metadata, retries, timeouts, and clear user consent before downloading binaries or productions.
- Add non-blocking background jobs for indexing, metadata refresh, downloads, and asset validation so the 3D interface remains responsive.
- Improve the UI around curation: featured productions, playlists, favorites, party/year/platform filters, screenshots, NFO text, and short contextual notes.
- Use machine screens as part of the core experience. The README says each machine screen should display landmark video; this would strongly reinforce the museum concept.
- Add controller and kiosk-mode support for exhibitions or couch viewing.
- Add structured logging and diagnostic export. Emulator launch issues are common; users need a way to share command lines, paths, and errors.
- Define a packaging strategy. Options include a developer mode, a Windows packaged release, and separately downloadable content packs.
- Optimize asset size and distribution. Source assets are tracked, compiled assets are ignored, and the local compiled folder is large. Decide whether release builds should ship compiled assets, build them on first run, or publish them as downloadable artifacts.
- Add CI for parser tests, command-builder tests, dependency checks, and repository hygiene checks.

## Suggested Near-Term Roadmap

1. Make startup reproducible.

   Centralize paths, fix requirements, document the exact setup flow, and add startup validation. This should come before adding more platforms.

2. Make one platform excellent.

   Amstrad CPC is the closest candidate. Finish `.dsk`/`.cpr` handling, launch validation, failure messages, and a small curated demo set with known-good launch profiles.

3. Connect Pouet metadata to the local library.

   Store Pouet IDs and metadata next to local artifacts, then show title/group/year/platform in the UI instead of relying on filenames.

4. Generalize platform adapters.

   Once the Amstrad path is robust, extract the same shape for MAME, Amiga, C64, and SNES rather than adding more special cases to `main.py`.

5. Add smoke tests.

   Test ROM parsing, Pouet classification, launch command construction, missing-binary handling, and path resolution. These tests can run without opening Harfang.

## Overall Assessment

Owl Arcade has a strong product idea and enough visual groundwork to justify continuing. Its main risk is not the 3D front-end; the visual direction is already coherent. The immediate risk is operational: a fresh user cannot reliably install, populate, validate, and launch productions without knowing the internals.

The best next move is to make the project boringly reproducible at the infrastructure level while preserving the more ambitious museum-like presentation. Once paths, dependencies, launch validation, and one complete platform are solid, the Pouet-backed demoscene library can become the project's real differentiator.
