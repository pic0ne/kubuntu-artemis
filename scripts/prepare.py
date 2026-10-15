#!/usr/bin/env python3
"""Download pinned upstream assets into the ignored, local assets directory."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
REPOSITORIES = {
    "Graphite-kde-theme": ("https://github.com/vinceliuice/Graphite-kde-theme.git", "5eb5020c327e133ff147cf1f47b5ab2807f11ae3"),
    "YAMIS": ("https://bitbucket.org/dirn-typo/yet-another-monochrome-icon-set.git", "227359bea788d55d202d9aad5f2daf63fe644cc3"),
    "kurve": ("https://github.com/luisbocanegra/kurve.git", "883cdbcf594f433009066ad577c21a5bd49589d4"),
    "kde-material-you-colors": ("https://github.com/luisbocanegra/kde-material-you-colors.git", "0b4d1502eca20bd12eb7b310eb8293a19030f397"),
}
FONT_REVISION = "803b7e23ec97ae58b6232ea76519a76d428ba268"
SANS_REVISION = "87b37a2daaed80fcb8e8ccb0085c4d72ddade12e"
DOWNLOADS = {
    "SourceCodePro-Regular.ttf": f"https://raw.githubusercontent.com/adobe-fonts/source-code-pro/{FONT_REVISION}/TTF/SourceCodePro-Regular.ttf",
    "SourceCodePro-Bold.ttf": f"https://raw.githubusercontent.com/adobe-fonts/source-code-pro/{FONT_REVISION}/TTF/SourceCodePro-Bold.ttf",
    "SourceSans3-Regular.ttf": f"https://raw.githubusercontent.com/adobe-fonts/source-sans/{SANS_REVISION}/TTF/SourceSans3-Regular.ttf",
    "SourceSans3-Semibold.ttf": f"https://raw.githubusercontent.com/adobe-fonts/source-sans/{SANS_REVISION}/TTF/SourceSans3-Semibold.ttf",
    "SourceSans3-Bold.ttf": f"https://raw.githubusercontent.com/adobe-fonts/source-sans/{SANS_REVISION}/TTF/SourceSans3-Bold.ttf",
    "artemis-eclipse.jpg": "https://images-assets.nasa.gov/image/art002e009301/art002e009301~orig.jpg",
    "artemis-earthset.jpg": "https://images-assets.nasa.gov/image/art002e009287/art002e009287~orig.jpg",
    "krohnkite.kwinscript": "https://codeberg.org/anametologin/Krohnkite/releases/download/0.9.10.0_alpha_2/krohnkite-0.9.10.0_alpha_2_f045ec0.kwinscript",
}
DIGESTS = {
    "SourceCodePro-Regular.ttf": "74bd80d3e42a08517cd7e1108ba3d86f2da29ac0f3065be95e0357956ab9db37",
    "SourceCodePro-Bold.ttf": "b2095e0d657e6d28dc32444a9dacabab0c9241d0bf39d96371756cc9bdbc3a5f",
    "SourceSans3-Regular.ttf": "4644c81b86ec9caaa76b634889968ed3c4f4f52f054855933acc7c2b21e53b0f",
    "SourceSans3-Semibold.ttf": "a3f4f8dcf343a8f24dc61951de93f3ba1558b15cd250ba24af8a40e957081b7d",
    "SourceSans3-Bold.ttf": "9214b9d95e4231c609802815c2646c98174e2102d0d37f88978a7f8e71006e6a",
    "artemis-eclipse.jpg": "4073cbcd74cf27eef45e9d5ba4c2a114e1d11f0e086691b1ce65f5f0561e8697",
    "artemis-earthset.jpg": "60280887a24f2e9e29133759f6195620862d42b8f39dfd3b80c18e16ad1ecbd5",
    "krohnkite.kwinscript": "0fac8a5255cefc977d5dd8c9e86c125db6d33ac6ffcbf1d8d384015f8fc0378c",
}
DEBS = [
    "cava=0.10.7+dfsg-1", "libiniparser4=4.2.6-1build1",
    "qml6-module-qtwebsockets=6.10.2-1", "python3-pip-whl=25.1.1+dfsg-1ubuntu2",
    "fastfetch=2.57.1+dfsg-1ubuntu1", "libyyjson0=0.12.0+ds-1",
]
PYTHON_PACKAGES = [
    "kde-material-you-colors==2.2.0", "materialyoucolor==3.0.4",
    "numpy==2.5.4", "pillow==12.3.0", "python-magic==0.4.27",
]


def run(*args, **kwargs):
    subprocess.run(args, check=True, **kwargs)


def check():
    missing = []
    for name, (_, revision) in REPOSITORIES.items():
        directory = ASSETS / name
        if not (directory / ".git").exists():
            missing.append(name)
            continue
        actual = subprocess.check_output(["git", "-C", str(directory), "rev-parse", "HEAD"], text=True).strip()
        if actual != revision:
            missing.append(name + " (revision mismatch)")
    for name in DOWNLOADS:
        if not (ASSETS / name).is_file():
            missing.append(name)
        elif hashlib.sha256((ASSETS / name).read_bytes()).hexdigest() != DIGESTS[name]:
            missing.append(name + " (checksum mismatch)")
    for package in DEBS:
        name, version = package.split("=", 1)
        if not list((ASSETS / "debs").glob(f"{name}_{version}_*.deb")):
            missing.append(package)
    for name in ["kde_material_you_colors", "materialyoucolor", "numpy", "PIL", "magic"]:
        if not (ASSETS / "python" / name).exists():
            missing.append("Python: " + name)
    if missing:
        raise SystemExit("Assets need preparation: " + ", ".join(missing))
    print("Pinned upstream assets and local runtime packages are available.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check cached assets without downloading or changing desktop settings.")
    args = parser.parse_args()
    if args.check:
        check()
        return
    if platform.machine() != "x86_64" or sys.version_info[:2] != (3, 14):
        raise SystemExit("The pinned local runtime targets x86_64 Kubuntu 26.04 with Python 3.14.")
    ASSETS.mkdir(exist_ok=True)
    for name, (url, revision) in REPOSITORIES.items():
        directory = ASSETS / name
        if directory.exists():
            actual = subprocess.check_output(["git", "-C", str(directory), "rev-parse", "HEAD"], text=True).strip()
            if actual != revision:
                raise SystemExit(f"Unexpected cached revision for {name}; move that directory aside before retrying.")
            continue
        run("git", "init", str(directory))
        run("git", "-C", str(directory), "remote", "add", "origin", url)
        run("git", "-C", str(directory), "-c", "credential.helper=", "fetch", "--depth=1", "origin", revision)
        run("git", "-C", str(directory), "checkout", "--detach", "FETCH_HEAD")
    for name, url in DOWNLOADS.items():
        destination = ASSETS / name
        if not destination.exists():
            partial = destination.with_suffix(destination.suffix + ".part")
            urllib.request.urlretrieve(url, partial)
            partial.replace(destination)
    debs = ASSETS / "debs"
    runtime = ASSETS / "runtime"
    debs.mkdir(exist_ok=True)
    runtime.mkdir(exist_ok=True)
    for package in DEBS:
        name, version = package.split("=", 1)
        if not list(debs.glob(f"{name}_{version}_*.deb")):
            run("apt", "download", package, cwd=debs)
    for deb in debs.glob("*.deb"):
        run("dpkg-deb", "-x", str(deb), str(runtime))
    wheels = list((runtime / "usr/share/python-wheels").glob("pip-*.whl"))
    if not wheels:
        raise SystemExit("The pip bootstrap wheel was not found in the downloaded runtime.")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(wheels[0])
    environment["PIP_CACHE_DIR"] = str(ASSETS / "pip-cache")
    run(sys.executable, "-m", "pip", "install", "--target", str(ASSETS / "python"), "--no-deps", *PYTHON_PACKAGES, env=environment)
    check()


if __name__ == "__main__":
    main()
