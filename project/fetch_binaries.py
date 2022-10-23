from os import getcwd, path, remove, makedirs
import requests
import zipfile


def fetch_binaries(harfang_version="3.2.4", architecture="win-x64"):
    bin_dest = path.join(getcwd(), "bin")
    binary_src_root = "https://github.com/harfang3d/harfang3d/releases/download/"

    # bin folder
    makedirs(name=bin_dest, exist_ok=True)

    # assetc
    assetc_url_src = binary_src_root + "v{a}/assetc-{b}-{c}.zip".format(a=harfang_version, b=architecture,  c=harfang_version)
    makedirs(name=path.join(bin_dest, "assetc"), exist_ok=True)
    tmp_zip_file = "assetc.zip"
    zip_file_dest = path.join(bin_dest, tmp_zip_file)

    if path.exists(zip_file_dest):
        remove(zip_file_dest)

    response = requests.get(assetc_url_src)
    open(zip_file_dest, "wb").write(response.content)

    with zipfile.ZipFile(zip_file_dest, 'r') as zip_ref:
        zip_ref.extractall(path.join(bin_dest, "assetc"))

    remove(zip_file_dest)

fetch_binaries()