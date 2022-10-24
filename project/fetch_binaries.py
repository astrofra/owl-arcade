from os import getcwd, path, remove, makedirs
from shutil import copyfileobj
import requests
import zipfile


def fetch_binaries(python_version="3.10.8", harfang_version="3.2.4"):
    bin_dest = path.join(getcwd(), "bin")
    binary_src_root = "https://github.com/harfang3d/harfang3d/releases/download/"

    # bin folder
    makedirs(name=bin_dest, exist_ok=True)

    # --
    # prepare assetc download
    assetc_url_src = binary_src_root + "v{a}/assetc-{b}-{c}.zip".format(a=harfang_version, b="win-x64", c=harfang_version)
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

    # --
    # python embeddable
    python_url_src = "https://www.python.org/ftp/python/{a}/python-{b}-embed-{c}.zip".format(a=python_version, b=python_version, c="amd64")
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

    # --
    # prepare harfang download
    # https://github.com/harfang3d/harfang3d/releases/download/v3.2.4/harfang-3.2.4-py3-none-win_amd64.whl
    hg_url_src = binary_src_root + "v{a}/harfang-{b}-py3-none-{c}.whl".format(a=harfang_version, b=harfang_version, c="win_amd64")
    makedirs(name=path.join(bin_dest, "harfang"), exist_ok=True)
    tmp_zip_file = "harfang.zip"
    zip_file_dest = path.join(bin_dest, tmp_zip_file)

    if path.exists(zip_file_dest):
        remove(zip_file_dest)

    # download harfang
    response = requests.get(hg_url_src)
    open(zip_file_dest, "wb").write(response.content)

    # unzip python
    with zipfile.ZipFile(zip_file_dest, 'r') as zip_ref:
        # zip_ref.extractall(path=path.join(bin_dest, "harfang"), members="harfang-3.2.4.data\purelib")
        # for file in zip_ref.namelist():
        #     if file.split("/")[-2] == 'harfang':
        #         zip_ref.extract(file, path.join(bin_dest, "harfang"))
        for member in zip_ref.namelist():
            filename = path.basename(member)
            # skip directories
            if not filename:
                continue
        
            # copy file (taken from zipfile's extract)
            source = zip_ref.open(member)
            target = open(path.join(path.join(bin_dest, "harfang"), filename), "wb")
            with source, target:
                copyfileobj(source, target)

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