import json

json_str = '''
{
    "success": true,
    "platforms": {
        "65": {
            "name": "BeOS",
            "icon": "k_beos.gif",
            "slug": "beos"
        },
        "66": {
            "name": "Linux",
            "icon": "k_linux.gif",
            "slug": "linux"
        },
        "67": {
            "name": "MS-Dos",
            "icon": "k_msdos.gif",
            "slug": "msdos"
        },
        "68": {
            "name": "Windows",
            "icon": "k_win.gif",
            "slug": "windows"
        },
        "69": {
            "name": "MS-Dos\/gus",
            "icon": "k_gus.gif",
            "slug": "msdosgus"
        },
        "70": {
            "name": "Atari ST",
            "icon": "k_atari_st.gif",
            "slug": "atarist"
        },
        "71": {
            "name": "Amiga AGA",
            "icon": "k_amiga_aga.gif",
            "slug": "amigaaga"
        },
        "72": {
            "name": "Atari STe",
            "icon": "k_atari_ste.gif",
            "slug": "atariste"
        },
        "73": {
            "name": "Amiga OCS\/ECS",
            "icon": "k_amiga.gif",
            "slug": "amigaocsecs"
        },
        "74": {
            "name": "Java",
            "icon": "k_java.gif",
            "slug": "java"
        },
        "75": {
            "name": "Playstation",
            "icon": "k_ps1.gif",
            "slug": "playstation"
        },
        "76": {
            "name": "Commodore 64",
            "icon": "k_commodore.gif",
            "slug": "commodore64"
        },
        "77": {
            "name": "Wild",
            "icon": "k_wild.gif",
            "slug": "wild"
        },
        "78": {
            "name": "Amstrad CPC",
            "icon": "k_cpc.gif",
            "slug": "amstradcpc"
        },
        "79": {
            "name": "Amiga PPC\/RTG",
            "icon": "k_amiga_ppc.gif",
            "slug": "amigappcrtg"
        },
        "80": {
            "name": "Atari Falcon 030",
            "icon": "k_atari_falcon.gif",
            "slug": "atarifalcon030"
        },
        "81": {
            "name": "Gameboy",
            "icon": "k_gameboy.gif",
            "slug": "gameboy"
        },
        "82": {
            "name": "ZX Spectrum",
            "icon": "k_zx.gif",
            "slug": "zxspectrum"
        },
        "83": {
            "name": "MacOSX PPC",
            "icon": "k_macb.gif",
            "slug": "macosxppc"
        },
        "84": {
            "name": "MacOS",
            "icon": "k_mac.gif",
            "slug": "macos"
        },
        "85": {
            "name": "Gameboy Advance",
            "icon": "k_gba.gif",
            "slug": "gameboyadvance"
        },
        "86": {
            "name": "Gameboy Color",
            "icon": "k_gbc.gif",
            "slug": "gameboycolor"
        },
        "87": {
            "name": "Dreamcast",
            "icon": "k_dreamcast.gif",
            "slug": "dreamcast"
        },
        "88": {
            "name": "SNES\/Super Famicom",
            "icon": "k_snes.gif",
            "slug": "snessuperfamicom"
        },
        "89": {
            "name": "SEGA Genesis\/Mega Drive",
            "icon": "k_megadrive.gif",
            "slug": "segagenesismegadrive"
        },
        "90": {
            "name": "Flash",
            "icon": "k_flash.gif",
            "slug": "flash"
        },
        "91": {
            "name": "Oric",
            "icon": "k_oric.gif",
            "slug": "oric"
        },
        "92": {
            "name": "Mobile Phone",
            "icon": "k_mobiles.gif",
            "slug": "mobilephone"
        },
        "93": {
            "name": "VIC 20",
            "icon": "k_vic20.gif",
            "slug": "vic20"
        },
        "94": {
            "name": "Playstation 2",
            "icon": "k_ps2.gif",
            "slug": "playstation2"
        },
        "95": {
            "name": "TI-8x (68k)",
            "icon": "k_ti8x.gif",
            "slug": "ti8x68k"
        },
        "96": {
            "name": "Atari TT 030",
            "icon": "k_tt.gif",
            "slug": "ataritt030"
        },
        "97": {
            "name": "Acorn",
            "icon": "k_acorn.gif",
            "slug": "acorn"
        },
        "98": {
            "name": "JavaScript",
            "icon": "k_js.gif",
            "slug": "javascript"
        },
        "99": {
            "name": "Alambik",
            "icon": "k_alambik.gif",
            "slug": "alambik"
        },
        "100": {
            "name": "NEC TurboGrafx\/PC Engine",
            "icon": "k_pce.gif",
            "slug": "necturbografxpcengine"
        },
        "101": {
            "name": "XBOX",
            "icon": "k_xbox.gif",
            "slug": "xbox"
        },
        "102": {
            "name": "PalmOS",
            "icon": "k_palmos.gif",
            "slug": "palmos"
        },
        "103": {
            "name": "Nintendo 64",
            "icon": "k_n64.gif",
            "slug": "nintendo64"
        },
        "104": {
            "name": "C16\/116\/plus4",
            "icon": "k_c16.gif",
            "slug": "c16116plus4"
        },
        "105": {
            "name": "PocketPC",
            "icon": "k_pocketpc.gif",
            "slug": "pocketpc"
        },
        "106": {
            "name": "PHP",
            "icon": "k_php.gif",
            "slug": "php"
        },
        "107": {
            "name": "MSX",
            "icon": "k_msx.gif",
            "slug": "msx"
        },
        "108": {
            "name": "GamePark GP32",
            "icon": "k_gamepark32.gif",
            "slug": "gameparkgp32"
        },
        "109": {
            "name": "Atari XL\/XE",
            "icon": "k_atari_xl_xe.gif",
            "slug": "atarixlxe"
        },
        "110": {
            "name": "Intellivision",
            "icon": "k_intellivision.gif",
            "slug": "intellivision"
        },
        "111": {
            "name": "Thomson",
            "icon": "k_thomson.gif",
            "slug": "thomson"
        },
        "112": {
            "name": "Apple II GS",
            "icon": "k_iigs.gif",
            "slug": "appleiigs"
        },
        "113": {
            "name": "SEGA Master System",
            "icon": "k_mastersystem.gif",
            "slug": "segamastersystem"
        },
        "114": {
            "name": "NES\/Famicom",
            "icon": "k_nes.gif",
            "slug": "nesfamicom"
        },
        "115": {
            "name": "Gamecube",
            "icon": "k_ngc.gif",
            "slug": "gamecube"
        },
        "116": {
            "name": "GamePark GP2X",
            "icon": "k_gp2x.gif",
            "slug": "gameparkgp2x"
        },
        "117": {
            "name": "Atari VCS",
            "icon": "k_atari_vcs.gif",
            "slug": "atarivcs"
        },
        "118": {
            "name": "Virtual Boy",
            "icon": "k_vb.gif",
            "slug": "virtualboy"
        },
        "119": {
            "name": "BK-0010\/11M",
            "icon": "k_bk.gif",
            "slug": "bk001011m"
        },
        "120": {
            "name": "Pokemon Mini",
            "icon": "k_pokemon.gif",
            "slug": "pokemonmini"
        },
        "121": {
            "name": "SEGA Game Gear",
            "icon": "k_gg.gif",
            "slug": "segagamegear"
        },
        "122": {
            "name": "Vectrex",
            "icon": "k_vectrex.gif",
            "slug": "vectrex"
        },
        "123": {
            "name": "iOS",
            "icon": "k_ipod.gif",
            "slug": "ios"
        },
        "124": {
            "name": "Playstation Portable",
            "icon": "k_psp.gif",
            "slug": "playstationportable"
        },
        "125": {
            "name": "Nintendo DS",
            "icon": "k_ds.gif",
            "slug": "nintendods"
        },
        "126": {
            "name": "Atari Jaguar",
            "icon": "k_jag.gif",
            "slug": "atarijaguar"
        },
        "127": {
            "name": "Wonderswan",
            "icon": "k_wonderswan.gif",
            "slug": "wonderswan"
        },
        "128": {
            "name": "NeoGeo Pocket",
            "icon": "k_neogeopocket.gif",
            "slug": "neogeopocket"
        },
        "131": {
            "name": "XBOX 360",
            "icon": "k_xbox360.gif",
            "slug": "xbox360"
        },
        "132": {
            "name": "Atari Lynx",
            "icon": "k_lynx.gif",
            "slug": "atarilynx"
        },
        "133": {
            "name": "C64 DTV",
            "icon": "k_dtv.gif",
            "slug": "c64dtv"
        },
        "134": {
            "name": "Amstrad Plus",
            "icon": "k_amplus.gif",
            "slug": "amstradplus"
        },
        "135": {
            "name": "FreeBSD",
            "icon": "k_freebsd.gif",
            "slug": "freebsd"
        },
        "136": {
            "name": "Solaris",
            "icon": "k_solaris.gif",
            "slug": "solaris"
        },
        "137": {
            "name": "Spectravideo 3x8",
            "icon": "k_sv.gif",
            "slug": "spectravideo3x8"
        },
        "138": {
            "name": "Apple II",
            "icon": "k_apple2.gif",
            "slug": "appleii"
        },
        "139": {
            "name": "MacOSX Intel",
            "icon": "k_macosx.gif",
            "slug": "macosxintel"
        },
        "140": {
            "name": "Playstation 3",
            "icon": "k_ps3.gif",
            "slug": "playstation3"
        },
        "141": {
            "name": "Nintendo Wii",
            "icon": "k_wii.gif",
            "slug": "nintendowii"
        },
        "142": {
            "name": "SGI\/IRIX",
            "icon": "k_sgi.gif",
            "slug": "sgiirix"
        },
        "143": {
            "name": "BBC Micro",
            "icon": "k_bbcmicro.gif",
            "slug": "bbcmicro"
        },
        "144": {
            "name": "MSX 2",
            "icon": "k_msx2.gif",
            "slug": "msx2"
        },
        "145": {
            "name": "SAM Coup\u00e9",
            "icon": "k_samcoupe.gif",
            "slug": "samcoup"
        },
        "146": {
            "name": "TRS-80\/CoCo\/Dragon",
            "icon": "k_coco.gif",
            "slug": "trs80cocodragon"
        },
        "147": {
            "name": "MSX Turbo-R",
            "icon": "k_msxt.gif",
            "slug": "msxturbor"
        },
        "148": {
            "name": "Enterprise",
            "icon": "k_ent.gif",
            "slug": "enterprise"
        },
        "149": {
            "name": "MSX 2 plus",
            "icon": "k_msx2p.gif",
            "slug": "msx2plus"
        },
        "150": {
            "name": "ZX-81",
            "icon": "k_zx81.gif",
            "slug": "zx81"
        },
        "151": {
            "name": "Android",
            "icon": "k_android.gif",
            "slug": "android"
        },
        "152": {
            "name": "mIRC",
            "icon": "k_mirc.gif",
            "slug": "mirc"
        },
        "153": {
            "name": "Commodore 128",
            "icon": "k_c128.gif",
            "slug": "commodore128"
        },
        "154": {
            "name": "Raspberry Pi",
            "icon": "k_raspi.gif",
            "slug": "raspberrypi"
        },
        "155": {
            "name": "Sharp MZ",
            "icon": "k_sharpmz.gif",
            "slug": "sharpmz"
        },
        "156": {
            "name": "ZX Enhanced",
            "icon": "k_zxenhanced.gif",
            "slug": "zxenhanced"
        },
        "157": {
            "name": "Animation\/Video",
            "icon": "k_video.gif",
            "slug": "animationvideo"
        },
        "158": {
            "name": "PICO-8",
            "icon": "k_pico8.png",
            "slug": "pico8"
        },
        "159": {
            "name": "TI-8x (Z80)",
            "icon": "k_tiz80.gif",
            "slug": "ti8xz80"
        },
        "160": {
            "name": "TIC-80",
            "icon": "k_tic80.png",
            "slug": "tic80"
        },
        "161": {
            "name": "Sinclair QL",
            "icon": "k_sinclairql.gif",
            "slug": "sinclairql"
        },
        "162": {
            "name": "Commodore PET",
            "icon": "k_cpet.gif",
            "slug": "commodorepet"
        },
        "163": {
            "name": "KC-85",
            "icon": "k_kc85.gif",
            "slug": "kc85"
        },
        "164": {
            "name": "Atari 7800",
            "icon": "k_atari7800.gif",
            "slug": "atari7800"
        }
    }
}
'''

data = json.loads(json_str)
names = [platform['name'] for platform in data['platforms'].values()]
print(names)
