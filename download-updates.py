#!/usr/bin/env python3
"""
Download the latest versions of all Minecraft plugins.

Sources used:
  - PaperMC API         (https://fill.papermc.io/v3)
  - EssentialsX Jenkins (https://ci.ender.zone)
  - Modrinth API        (https://api.modrinth.com/v2)
  - Spiget API          (https://api.spiget.org/v2) — unofficial mirror

NOTE: dev.bukkit.org direct downloads return 403 — plugins previously
      sourced from there have been remapped to Spiget/Modrinth below.
      CoreProtect downloads the Community Edition (CE) from Modrinth.
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import requests
from pathlib import Path
from urllib.parse import urlparse

OUTPUT_DIR = Path("updates/plugins")
PAPER_DIR = Path("updates")

API_TIMEOUT = 30
USER_AGENT = "plugin-updater/1.0 (github.com/TheOutcastsMC)"
SPIGET_HEADERS = {"User-Agent": USER_AGENT}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_filename(display_name: str, version: str) -> str:
    return display_name.replace(" ", "") + "-" + version + ".jar"


def download_file(
    url: str,
    dest_dir: Path,
    filename: str | None = None,
    session: requests.Session | None = None,
) -> Path:
    s = session or requests.Session()
    s.headers.setdefault("User-Agent", USER_AGENT)

    resp = s.get(url, stream=True, allow_redirects=True, timeout=60)
    resp.raise_for_status()

    if filename is None:
        cd = resp.headers.get("Content-Disposition", "")
        if "filename=" in cd:
            filename = cd.split("filename=")[-1].strip("\"' ")
        else:
            filename = Path(urlparse(resp.url).path).name or "download.jar"

    dest = dest_dir / filename
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=65536):
            fh.write(chunk)
    print(f"  -> {dest}")
    return dest


# ---------------------------------------------------------------------------
# Source: PaperMC
# ---------------------------------------------------------------------------

def download_paper() -> None:
    print("\n[Paper]")
    base = "https://fill.papermc.io/v3/projects/paper"

    # Get latest supported version
    all_versions = requests.get(
        f"{base}/versions", timeout=API_TIMEOUT
    ).json()["versions"]
    supported = [
        v for v in all_versions
        if v["version"].get("support", {}).get("status") == "SUPPORTED"
    ]
    latest_ver = (supported or all_versions)[-1]["version"]["id"]

    # Get latest build for that version
    build = requests.get(
        f"{base}/versions/{latest_ver}/builds/latest",
        timeout=API_TIMEOUT,
    ).json()
    build_num = build["id"]
    download = next(iter(build["downloads"].values()))

    print(f"  Paper {latest_ver} build {build_num}")
    download_file(download["url"], PAPER_DIR, download["name"])


# ---------------------------------------------------------------------------
# Source: EssentialsX Jenkins
# ---------------------------------------------------------------------------

ESSENTIALS_MODULES = ("EssentialsX-", "EssentialsXChat-", "EssentialsXSpawn-")


def download_essentialsx() -> None:
    print("\n[EssentialsX]")
    jenkins_base = "https://ci.ender.zone/job/EssentialsX/lastSuccessfulBuild"

    data = requests.get(f"{jenkins_base}/api/json", timeout=API_TIMEOUT).json()
    for artifact in data.get("artifacts", []):
        name = artifact["fileName"]
        if any(name.startswith(m) for m in ESSENTIALS_MODULES):
            url = f"{jenkins_base}/artifact/{artifact['relativePath']}"
            print(f"  {name}")
            download_file(url, OUTPUT_DIR, name)


# ---------------------------------------------------------------------------
# Source: Modrinth
# ---------------------------------------------------------------------------

def download_modrinth(
    project_id: str,
    display_name: str,
    file_prefixes: tuple[str, ...] | None = None,
    loaders: tuple[str, ...] | None = None,
) -> None:
    print(f"\n[{display_name}] (Modrinth)")
    params: dict = {"limit": 5}
    if loaders:
        params["loaders"] = json.dumps(list(loaders))
    else:
        params["version_type"] = "release"

    versions = requests.get(
        f"https://api.modrinth.com/v2/project/{project_id}/version",
        params=params,
        timeout=API_TIMEOUT,
    ).json()

    if not versions:
        versions = requests.get(
            f"https://api.modrinth.com/v2/project/{project_id}/version",
            params={"limit": 1},
            timeout=API_TIMEOUT,
        ).json()

    latest = versions[0]
    version = latest["version_number"]
    print(f"  {display_name} {version}")

    if file_prefixes is None:
        primary = next(
            (f for f in latest["files"] if f.get("primary")),
            latest["files"][0],
        )
        download_file(
            primary["url"], OUTPUT_DIR, make_filename(display_name, version)
        )
    else:
        for prefix in file_prefixes:
            match = next(
                (f for f in latest["files"]
                 if f["filename"].startswith(prefix)),
                None,
            )
            if match:
                download_file(match["url"], OUTPUT_DIR, match["filename"])
            else:
                print(f"  WARNING: no file matching '{prefix}' in version"
                      f" {version}")


# ---------------------------------------------------------------------------
# Source: GitHub Releases
# ---------------------------------------------------------------------------

def download_github(repo: str, display_name: str) -> None:
    print(f"\n[{display_name}] (GitHub: {repo})")
    release = requests.get(
        f"https://api.github.com/repos/{repo}/releases/latest",
        timeout=API_TIMEOUT,
    ).json()
    version = release["tag_name"]
    asset = next(
        (a for a in release["assets"]
         if a["name"].endswith(".jar") and "sources" not in a["name"]),
        None,
    )
    if not asset:
        print(f"  WARNING: no .jar asset found in release {version}")
        return
    print(f"  {display_name} {version}")
    download_file(
        asset["browser_download_url"],
        OUTPUT_DIR,
        make_filename(display_name, version),
    )


GITHUB_PLUGINS = [
    # (repo,                    display_name)
    ("dmulloy2/ProtocolLib",   "ProtocolLib"),
    ("jacob1/dynmap",   "Dynmap"),
]


# ---------------------------------------------------------------------------
# Source: GitHub Packages (Maven)
# ---------------------------------------------------------------------------

def download_github_package(
    repo: str,
    group_id: str,
    artifact_id: str,
    version: str,
    display_name: str,
) -> None:
    print(f"\n[{display_name}] (GitHub Packages: {repo})")
    status = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True
    )
    if "read:packages" not in (status.stdout + status.stderr):
        raise RuntimeError(
            "gh token is missing the 'read:packages' scope.\n"
            "  Fix: gh auth refresh -s read:packages"
        )
    token = subprocess.check_output(
        ["gh", "auth", "token"], text=True
    ).strip()
    username = subprocess.check_output(
        ["gh", "api", "user", "--jq", ".login"], text=True
    ).strip()
    session = requests.Session()
    session.auth = (username, token)
    base = (
        f"https://maven.pkg.github.com/{repo}"
        f"/{group_id.replace('.', '/')}/{artifact_id}/{version}"
    )
    meta = session.get(f"{base}/maven-metadata.xml", timeout=API_TIMEOUT)
    meta.raise_for_status()
    root = ET.fromstring(meta.text)
    sv = root.find(
        ".//snapshotVersions/snapshotVersion[extension='jar']/value"
    )
    resolved = sv.text if sv is not None else version
    print(f"  {display_name} {resolved}")
    download_file(
        f"{base}/{artifact_id}-{resolved}.jar",
        OUTPUT_DIR,
        make_filename(display_name, version),
        session=session,
    )


GITHUB_PACKAGE_PLUGINS = [
    # (repo,                   group_id,         artifact_id,  version,           display_name)
    ("nikosgram/gringotts",   "minecraftwars",   "gringotts",  "3.0.1-SNAPSHOT",  "Gringotts"),
]


# ---------------------------------------------------------------------------
# Source: Spiget (SpigotMC mirror)
# ---------------------------------------------------------------------------

def download_spiget(
    resource_id: int, display_name: str, skipped: list[str]
) -> None:
    print(f"\n[{display_name}] (Spiget #{resource_id})")

    info = requests.get(
        f"https://api.spiget.org/v2/resources/{resource_id}",
        headers=SPIGET_HEADERS,
        timeout=API_TIMEOUT,
    ).json()

    if info.get("external"):
        url = f"https://www.spigotmc.org/resources/{resource_id}/"
        print(f"  SKIPPED: external resource — download manually from {url}")
        skipped.append(f"{display_name}: external — {url}")
        return
    if info.get("premium"):
        url = f"https://www.spigotmc.org/resources/{resource_id}/"
        print(f"  SKIPPED: premium resource — purchase manually from {url}")
        skipped.append(f"{display_name}: premium — {url}")
        return

    ver = requests.get(
        f"https://api.spiget.org/v2/resources/{resource_id}/versions/latest",
        headers=SPIGET_HEADERS,
        timeout=API_TIMEOUT,
    ).json()
    version = ver.get("name", "unknown")
    print(f"  {display_name} {version}")

    session = requests.Session()
    session.headers.update(SPIGET_HEADERS)
    download_file(
        f"https://api.spiget.org/v2/resources/{resource_id}/download",
        OUTPUT_DIR,
        filename=make_filename(display_name, version),
        session=session,
    )


# ---------------------------------------------------------------------------
# Plugin lists
# ---------------------------------------------------------------------------

MODRINTH_PLUGINS = [
    # (project_id,  display_name,            file_prefixes or None,  loaders or None)
    ("Lu3KuzdV",   "CoreProtect",            None,                   None),
    ("O4o4mKaq",   "GriefPrevention",        None,                   None),
    ("ijC5dDkD",   "QuickShop-Hikari",       (
        "QuickShop-Hikari",
        "Addon-Dynmap",
        "Addon-ShopItemOnly",
        "Compat-GriefPrevention",
        "Compat-WorldGuard",
        "Compat-OpenInv",
    ),                                                                None),
    # Previously on dev.bukkit.org — remapped to Modrinth:
    ("1u6JkXh5",   "WorldEdit",              None,                   None),
    ("DKY9btbd",   "WorldGuard",             None,                   None),
    ("3wmN97b8",   "Multiverse-Core",        None,                   None),
    ("qvdtDX3s",   "Multiverse-Inventories", None,                   None),
    ("8VMk6P0I",   "Multiverse-Portals",     None,                   None),
    ("1UlvXbzL",   "OpenInv",                None,                   None),
    # External on Spiget — remapped to Modrinth:
    ("HFTnFHKn",   "AntiPopup",              None,                   None),
    ("ZfddU72x",   "WanderingTrades",        None,                   None),
    ("gG7VFbG0",   "TAB",                    None,                   None),
]

SPIGET_PLUGINS = [
    # (resource_id,  display_name)
    # Previously on dev.bukkit.org — remapped to Spiget:
    (71699,  "DropHeads"),
    # SpigotMC plugins:
    (89720,  "AntiBookBan"),
    (2237,   "Armor Stand Tools"),
    (81534,  "Chunky"),
    (82365,  "DoubleShulkerShells"),
    (28140,  "LuckPerms"),
    (60623,  "SleepMost"),
    (80692,  "SurvivalInvisiFrames"),
    (34315,  "Vault"),
    # (127018,  "TabList"),
    (98376,  "Dynmap-GriefPrevention"),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    skipped: list[str] = []

    def run(label: str, fn, *args):
        try:
            fn(*args)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            errors.append(f"{label}: {exc}")

    run("Paper", download_paper)

    run("EssentialsX", download_essentialsx)

    for pid, name, prefixes, loaders in MODRINTH_PLUGINS:
        run(name, download_modrinth, pid, name, prefixes, loaders)

    for rid, name in SPIGET_PLUGINS:
        run(name, download_spiget, rid, name, skipped)

    for repo, name in GITHUB_PLUGINS:
        run(name, download_github, repo, name)

    for repo, group, artifact, version, name in GITHUB_PACKAGE_PLUGINS:
        run(name, download_github_package, repo, group, artifact, version, name)

    print("\n" + "=" * 50)
    if skipped:
        print(f"{len(skipped)} skipped (manual download required):")
        for s in skipped:
            print(f"  - {s}")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    elif not skipped:
        print("All downloads completed successfully.")


if __name__ == "__main__":
    main()
