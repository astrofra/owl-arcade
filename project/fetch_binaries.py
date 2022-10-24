from os import getcwd, path, remove, makedirs
import requests
import zipfile


def fetch_binaries(python_version="3.10.8", harfang_version="3.2.4", architecture="win-x64"):
    bin_dest = path.join(getcwd(), "bin")
    binary_src_root = "https://github.com/harfang3d/harfang3d/releases/download/"

    # bin folder
    makedirs(name=bin_dest, exist_ok=True)

    # prepare assetc download
    assetc_url_src = binary_src_root + "v{a}/assetc-{b}-{c}.zip".format(a=harfang_version, b=architecture, c=harfang_version)
    makedirs(name=path.join(bin_dest, "assetc"), exist_ok=True)
    tmp_zip_file = "assetc.zip"
    zip_file_dest = path.join(bin_dest, tmp_zip_file)

    if path.exists(zip_file_dest):
        remove(zip_file_dest)

    # download assetc
    response = requests.get(assetc_url_src)
    open(zip_file_dest, "wb").write(response.content)

    # unzip assetc
    with zipfile.ZipFile(zip_file_dest, 'r') as zip_ref:
        zip_ref.extractall(path.join(bin_dest, "assetc"))

    # cleanup
    remove(zip_file_dest)

    # python embeddable
    python_url_src = "https://www.python.org/ftp/python/{a}/python-{b}-embed-amd64.zip".format(a=python_version, b=python_version)
    makedirs(name=path.join(bin_dest, "python"), exist_ok=True)
    tmp_zip_file = "python.zip"
    zip_file_dest = path.join(bin_dest, tmp_zip_file)

    if path.exists(zip_file_dest):
        remove(zip_file_dest)

    # download python
    response = requests.get(python_url_src)
    open(zip_file_dest, "wb").write(response.content)

    # unzip python
    with zipfile.ZipFile(zip_file_dest, 'r') as zip_ref:
        zip_ref.extractall(path.join(bin_dest, "python"))

    # cleanup
    remove(zip_file_dest)

    # overwrite pth file
    pth_file = name=path.join(bin_dest, "python", "python{a}{b}._pth").format(a=python_version.split(".")[0], b=python_version.split(".")[1])
    remove(pth_file)

    file_str = ""
    file_str += "python{a}{b}.zip".format(a=python_version.split(".")[0], b=python_version.split(".")[1]) + "\n"
    file_str += "." + "\n"
    file_str += "..\\" + "\n"
    file_str += "..\\harfang\\" + "\n"
    file_str += "..\\xmltodict\\" + "\n"
    file_str += "..\\tqdm\\" + "\n"
    file_str += "..\\..\\project\\" + "\n"

    with open(pth_file, 'w') as f:
        f.write(file_str)

fetch_binaries()