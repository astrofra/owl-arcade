try:
    import harfang as hg
except:
    pass
from classic_levenshtein import levenshtein_distance
from os import getcwd, path, pardir, listdir

from fetch_binaries import fetch_mame_binary
from commands import start_amiga, start_mame, start_amstrad_cpc, init_temp_folder
from rom_parser import parse_apple_2_games, parse_trs_80_games, parse_amstrad_cpc_games, parse_mame_games, parse_amiga_games

# 3D models by : Georg Klein, Darren.Hogan, Dekogon, kotkozyrkov, pbr3d, Gamereadyassets, cggoor, Shrednector, Tornado Studio, Attilad, abramsdesign
# Sounds by : DWOBoyle, neezen, schluppipuppie, Speedenza

def sfx_play_woosh(hg):
    snd_ref = hg.LoadWAVSoundAsset('sfx/sfx_woosh_high.wav')  # WAV 44.1kHz 16bit mono
    src_ref = hg.PlayStereo(snd_ref, hg.StereoSourceState(1, hg.SR_Once))


def machine_get_name(machine):
    return machine.get('name')


def scene_load_machine_assets_from_index(hg, scene, res, machines, current_machine_idx):
    if machines[current_machine_idx]['path'] is not None:
        n, _ = hg.CreateInstanceFromAssets(scene, hg.Mat4.Identity, "machines/" + machines[current_machine_idx]['path'], res, hg.GetForwardPipelineInfo())
        return n
    else:
        return scene.CreateNode()


def scene_animate_machines(hg, dt, res, scene, camera_parent_node, slot_change_speed, machine_slot, slot_idx, slot_change_dir, machines, current_machine_idx):
    if slot_change_dir != 0:
        current_machine_idx = (current_machine_idx + slot_change_dir) % len(machines)
        old_slot_idx = slot_idx
        slot_idx = (slot_idx + 1)%2
        if machine_slot[slot_idx]['node'] is not None:
            scene.DestroyNode(machine_slot[slot_idx]['node'])
            scene.GarbageCollect()
        machine_slot[slot_idx]['node'] = scene_load_machine_assets_from_index(hg, scene, res, machines, current_machine_idx)
        machine_slot[slot_idx]['node'].GetTransform().SetPos(machine_slot[slot_idx]['pos'])

        # swap slots and move camera (if needed)
        if (slot_change_dir > 0 and machine_slot[old_slot_idx]['pos'].x > machine_slot[slot_idx]['pos'].x) or (slot_change_dir < 0 and machine_slot[old_slot_idx]['pos'].x < machine_slot[slot_idx]['pos'].x):
            tmp_pos = machine_slot[slot_idx]['pos']
            machine_slot[slot_idx]['pos'] = machine_slot[old_slot_idx]['pos']
            machine_slot[old_slot_idx]['pos'] = tmp_pos
            machine_slot[slot_idx]['node'].GetTransform().SetPos(machine_slot[slot_idx]['pos'])
            if machine_slot[old_slot_idx]['node'] is not None:
                machine_slot[old_slot_idx]['node'].GetTransform().SetPos(machine_slot[old_slot_idx]['pos'])
            camera_parent_node.GetTransform().SetPos(machine_slot[old_slot_idx]['pos'])

        slot_change_dir = 0

        sfx_play_woosh(hg)

    camera_velocity = dt_step(hg.time_to_sec_f(dt) * slot_change_speed, camera_parent_node.GetTransform().GetPos(), machine_slot[slot_idx]['pos'])
    camera_parent_node.GetTransform().SetPos(camera_parent_node.GetTransform().GetPos() + camera_velocity)

    return machine_slot, slot_idx, slot_change_dir, current_machine_idx, camera_velocity


def draw_machine_name(hg, view_id, res_x, res_y, font, font_prg, text_uniform_values_shadows, text_uniform_values, text_render_state, machine_name):
    # 2D view, note that only the depth buffer is cleared
    hg.SetView2D(view_id, 0, 0, res_x, res_y, -1, 1, hg.CF_Depth, hg.ColorI(32, 32, 32), 1, 0)

    hg.DrawText(view_id, font, machine_name, font_prg, 'u_tex', 0, hg.Mat4.Identity,
                hg.Vec3(res_x * 0.95, res_y / 1.35, 0) + hg.Vec3(res_x / 500.0, res_y / 500.0, 0),
                hg.DTHA_Right, hg.DTVA_Center, text_uniform_values_shadows, [], text_render_state)

    hg.DrawText(view_id, font, machine_name, font_prg, 'u_tex', 0, hg.Mat4.Identity,
                hg.Vec3(res_x * 0.95, res_y / 1.35, 0),
                hg.DTHA_Right, hg.DTVA_Center, text_uniform_values, [], text_render_state)


def draw_game_selection(hg, view_id, res_x, res_y, y_ratio, font, font_prg, text_uniform_values_shadows, text_uniform_values, text_render_state, games, idx):
    # 2D view, note that only the depth buffer is cleared
    hg.SetView2D(view_id, 0, 0, res_x, res_y, -1, 1, hg.CF_Depth, hg.ColorI(32, 32, 32), 1, 0)
    selector_size = 10
    shadow_offset = hg.Vec3(res_x / 500.0, res_y / 500.0, 0)

    if len(games) > 0:
        for i in range(selector_size):
            j = (i + idx) % len(games)
            game_title = games[j]['title']
            hg.DrawText(view_id, font, game_title, font_prg, 'u_tex', 0, hg.Mat4.Identity,
                        hg.Vec3(res_x * 0.05, res_y * (0.45 + (i * 0.04 * y_ratio)), 0) + shadow_offset,
                        hg.DTHA_Left, hg.DTVA_Center, text_uniform_values_shadows, [], text_render_state)

            hg.DrawText(view_id, font, game_title, font_prg, 'u_tex', 0, hg.Mat4.Identity,
                        hg.Vec3(res_x * 0.05, res_y * (0.45 + (i * 0.04 * y_ratio)), 0),
                        hg.DTHA_Left, hg.DTVA_Center, text_uniform_values, [], text_render_state)

        # draw cursor
        hg.DrawText(view_id, font, '>>', font_prg, 'u_tex', 0, hg.Mat4.Identity,
                    hg.Vec3(res_x * 0.045, res_y * 0.45, 0) + shadow_offset,
                    hg.DTHA_Right, hg.DTVA_Center, text_uniform_values_shadows, [], text_render_state)

        hg.DrawText(view_id, font, '>>', font_prg, 'u_tex', 0, hg.Mat4.Identity,
                    hg.Vec3(res_x * 0.045, res_y * 0.45, 0),
                    hg.DTHA_Right, hg.DTVA_Center, text_uniform_values, [], text_render_state)


def dt_step(dt, vec_src, vec_dst):
    return (vec_dst - vec_src) * dt


def main():
    machines = [
                {'name': 'Commodore 64', 'path': 'commodore_64.scn', 'games': [], 'parser': None, 'launcher': None},
                {'name': 'Super Nintendo', 'path': 'nintendo_snes.scn', 'games': [], 'parser': None, 'launcher': None},
                {'name': 'Apple //e', 'path': 'apple_2_e.scn', 'games': [], 'parser': parse_apple_2_games, 'launcher': None},
                {'name': 'Atari VCS 2600', 'path': 'atari_vcs_2600.scn', 'games': [], 'parser': None, 'launcher': None},
                {'name': 'Tandy TRS-80 III', 'path': 'tandy_trs_80.scn', 'games': [], 'parser': parse_trs_80_games, 'launcher': None},
                {'name': 'Amstrad CPC 464', 'path': 'amstrad_cpc_464.scn', 'games': [], 'parser': parse_amstrad_cpc_games, 'launcher': start_amstrad_cpc},
                {'name': 'Nec PC/FX', 'path': 'nec_pcfx.scn', 'games': [], 'parser': None, 'launcher': None},
                {'name': 'Arcade', 'path': None, 'games': [], 'parser': parse_mame_games, 'launcher': start_mame},
                {'name': 'Commodore Amiga', 'path': 'commodore_amiga_500.scn', 'games': [], 'parser': parse_amiga_games, 'launcher': start_amiga},
                ]

    machines.sort(key=machine_get_name)

    # start_amstrad_cpc(['Wild Streets (1990)(Titus).zip'])
    # exit()

    # fetch_mame_binary(path.join("bin", "emulators", "mame"))

    for idx, machine in enumerate(machines):
        if machines[idx]['parser'] is not None:
            machines[idx]['games'] = machines[idx]['parser']()
        else:
            machines[idx]['games'] = []
    # games = []
    # games = parse_mame_roms()
    # games = parse_apple_2_games()

    # games = machines[0]['games']
    # print([machines[0]['launcher'](games[0]['filename'])])

    game_selector_idx = 0

    hg.InputInit()
    hg.AudioInit()
    hg.WindowSystemInit()

    res_ref_x, res_ref_y = 1280, 720
    res_multiplier = 1.0
    res_x, res_y = int(res_ref_x * res_multiplier), int(res_ref_y * res_multiplier)
    win = hg.NewWindow('OWL ARCADE', res_x, res_y, 32, 0) # hg.WV_Fullscreen)
    hg.RenderInit(win)
    hg.RenderReset(res_x, res_y, hg.RF_MSAA4X | hg.RF_FlipAfterRender | hg.RF_FlushAfterRender | hg.RF_MaxAnisotropy)

    pipeline = hg.CreateForwardPipeline()
    res = hg.PipelineResources()

    hg.AddAssetsFolder("project/assets")

    # load font and shader program
    glyphs_str = ""
    glyphs_str += "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ "
    glyphs_str += "¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"

    font_machine_name = hg.LoadFontFromAssets('fonts/ROBOTO-THIN.TTF', int(96 * res_x / res_ref_x))
    font_game_title = hg.LoadFontFromAssets('fonts/ROBOTO-MEDIUM.TTF', int(24 * res_x / res_ref_x), 1024, 1, glyphs_str)
    font_prg = hg.LoadProgramFromAssets('core/shader/font')

    # text uniforms and render state
    text_uniform_values = [hg.MakeUniformSetValue('u_color', hg.Vec4(1, 1, 1))]
    text_uniform_values_shadows = [hg.MakeUniformSetValue('u_color', hg.Vec4(0, 0, 0, 0.5))]
    text_render_state = hg.ComputeRenderState(hg.BM_Alpha, hg.DT_Always, hg.FC_Disabled)

    # load scene
    scene = hg.Scene()
    hg.LoadSceneFromAssets("background.scn", scene, res, hg.GetForwardPipelineInfo())

    # AAA pipeline
    pipeline_aaa_config = hg.ForwardPipelineAAAConfig()
    pipeline_aaa = hg.CreateForwardPipelineAAAFromAssets("core", pipeline_aaa_config, hg.BR_Equal, hg.BR_Equal)

    pipeline_aaa_config.sample_count = 1
    pipeline_aaa_config.temporal_aa_weight = 0.01

    pipeline_aaa_config.bloom_threshold = 0.550
    pipeline_aaa_config.bloom_bias = 0.250
    pipeline_aaa_config.bloom_intensity = 0.700

    pipeline_aaa_config.exposure = 1.1
    pipeline_aaa_config.gamma = 2.1

    keyboard = hg.Keyboard('raw')

    current_machine_idx = 0

    machine_slot_width = 1.0  # meters
    machine_slot = [{'node': None, 'pos': hg.Vec3(-machine_slot_width, 0, 0)},
                    {'node': None, 'pos': hg.Vec3(machine_slot_width, 0, 0)}]
    slot_idx = 1
    slot_change_speed = 2.0
    slot_change_dir = 1

    camera_parent_node = scene.CreateNode()
    camera_parent_node.SetTransform(scene.CreateTransform())

    camera_node = scene.GetNode("Camera")
    scene.SetCurrentCamera(camera_node)
    camera_node.GetTransform().SetParent(camera_parent_node)
    scene.GetNode("Light").GetTransform().SetParent(camera_parent_node)

    # main loop
    frame = 0
    long_press_timeout = 0
    processes = []

    while not hg.ReadKeyboard().Key(hg.K_Escape):
        render_was_reset, res_x, res_y = hg.RenderResetToWindow(win, res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)

        if 0:
            dt = hg.time_from_sec_f(1.0 / 60.0)
        else:
            dt = hg.time_from_sec_f(min(1.0 / 60.0, hg.time_to_sec_f(hg.TickClock())))

        keyboard.Update()

        if keyboard.Pressed(hg.K_Left):
            slot_change_dir = -1
        elif keyboard.Pressed(hg.K_Right):
            slot_change_dir = 1

        if keyboard.Pressed(hg.K_Up):
            game_selector_idx -= 1
        elif keyboard.Pressed(hg.K_Down):
            game_selector_idx += 1

        if keyboard.Down(hg.K_Up):
            long_press_timeout += 1
            if long_press_timeout > 15:
                game_selector_idx -= 1
        elif keyboard.Down(hg.K_Down):
            long_press_timeout += 1
            if long_press_timeout > 15:
                game_selector_idx += 1
        else:
            long_press_timeout = 0

        games = machines[current_machine_idx]['games']

        if len(games) > 0:
            game_selector_idx = game_selector_idx % len(games)
        else:
            game_selector_idx = 0

        machine_slot, slot_idx, slot_change_dir, current_machine_idx, camera_velocity = scene_animate_machines(hg, dt, res, scene, camera_parent_node, slot_change_speed, machine_slot, slot_idx, slot_change_dir, machines, current_machine_idx)

        if camera_velocity is not None and hg.Len(camera_velocity) < 0.01:
            if keyboard.Pressed(hg.K_Space):
                if machines[current_machine_idx]['launcher'] is not None:
                    processes = [machines[current_machine_idx]['launcher'](games[game_selector_idx]['filename'])]

        scene.Update(dt)
        view_id, pass_id = hg.SubmitSceneToPipeline(0, scene, hg.IntRect(0, 0, res_x, res_y), True, pipeline, res, pipeline_aaa, pipeline_aaa_config, frame)

        draw_machine_name(hg, view_id, res_x, res_y, font_machine_name, font_prg, text_uniform_values_shadows, text_uniform_values, text_render_state, machines[current_machine_idx]['name'])

        draw_game_selection(hg, view_id, res_x, res_y, res_y / res_ref_y, font_game_title, font_prg, text_uniform_values_shadows, text_uniform_values, text_render_state, games, game_selector_idx)


        frame = hg.Frame()
        hg.UpdateWindow(win)

        for process in processes:
            if process is not None:
                process.wait()

    hg.RenderShutdown()
    hg.DestroyWindow(win)


main()
