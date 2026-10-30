import os
import re
from datetime import datetime

VERSION_PATTERNS = [
    # 1. Separator + 'v'/'V' + digits: MyScene_v001.blend, Shot-V2.blend, Test.v03.blend
    re.compile(r"^(?P<stem>.+?)[._-][vV](?P<num>\d+)(?P<ext>\.blend\d*)$", re.IGNORECASE),
    # 2. Separator + digits: MyScene_001.blend, Test.002.blend
    re.compile(r"^(?P<stem>.+?)[._-](?P<num>\d+)(?P<ext>\.blend\d*)$"),
    # 3. Direct 'v'/'V' + digits: MyScenev001.blend
    re.compile(r"^(?P<stem>.+?)[vV](?P<num>\d+)(?P<ext>\.blend\d*)$"),
]


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_mtime(timestamp: float) -> str:
    if timestamp <= 0:
        return ""
    try:
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("Today %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def parse_filename(filename: str, include_blend1: bool = False):
    """
    Parse a filename to extract stem, version number, and extension.
    Returns None if the file is not a valid blend file.
    """
    lower = filename.lower()
    if not lower.endswith(".blend") and not (include_blend1 and ".blend" in lower):
        return None

    # Check version patterns
    for pat in VERSION_PATTERNS:
        m = pat.match(filename)
        if m:
            stem = m.group("stem")
            num_str = m.group("num")
            ext = m.group("ext")
            if not include_blend1 and ext.lower() != ".blend":
                continue
            return {
                "stem": stem,
                "version_num": int(num_str),
                "raw_version": num_str,
                "padding": len(num_str),
                "ext": ext,
                "is_versioned": True,
            }

    # Standalone unversioned .blend file
    if lower.endswith(".blend"):
        return {
            "stem": filename[:-6],
            "version_num": 0,
            "raw_version": "",
            "padding": 0,
            "ext": ".blend",
            "is_versioned": False,
        }

    return None


def scan_directory(dirpath: str, show_unversioned: bool = True, include_blend1: bool = False, sort_by: str = 'NAME_ASC'):
    """
    Scan a directory for .blend files and group them into scene families.
    Returns a list of dicts describing scene families and their versions.
    """
    if not dirpath or not os.path.isdir(dirpath):
        return []

    try:
        entries = [e for e in os.scandir(dirpath) if e.is_file()]
    except OSError:
        return []

    # Map stem -> list of file version dicts
    groups = {}

    for entry in entries:
        info = parse_filename(entry.name, include_blend1=include_blend1)
        if not info:
            continue

        if not info["is_versioned"] and not show_unversioned:
            continue

        try:
            stat = entry.stat()
            mtime = stat.st_mtime
            size = stat.st_size
        except OSError:
            mtime = 0.0
            size = 0

        item_data = {
            "filename": entry.name,
            "version_num": info["version_num"],
            "raw_version": info["raw_version"],
            "is_versioned": info["is_versioned"],
            "version_label": f"v{info['raw_version']}" if info["is_versioned"] else "base",
            "size_str": format_file_size(size),
            "mtime": mtime,
            "mtime_str": format_mtime(mtime),
        }

        groups.setdefault(info["stem"], []).append(item_data)

    results = []
    for stem, versions in groups.items():
        # Sort versions: unversioned first (0), then version numbers ascending
        versions.sort(key=lambda v: (v["version_num"], v["mtime"]))

        latest = versions[-1]
        max_mtime = max((v["mtime"] for v in versions), default=0.0)

        results.append({
            "stem": stem,
            "name": stem,
            "latest_filename": latest["filename"],
            "latest_version_label": latest["version_label"],
            "latest_version_num": latest["version_num"],
            "is_versioned": latest["is_versioned"],
            "version_count": len(versions),
            "latest_filesize": latest["size_str"],
            "latest_mtime": format_mtime(max_mtime) if max_mtime > 0 else latest["mtime_str"],
            "latest_mtime_raw": max_mtime,
            "versions": list(reversed(versions)),  # reverse so newest older versions are first
        })

    # Sort scene groups
    if sort_by in {'NAME_ASC', 'NAME'}:
        results.sort(key=lambda g: g["name"].lower())
    elif sort_by == 'NAME_DESC':
        results.sort(key=lambda g: g["name"].lower(), reverse=True)
    elif sort_by in {'DATE_DESC', 'DATE'}:
        results.sort(key=lambda g: g["latest_mtime_raw"], reverse=True)
    elif sort_by == 'DATE_ASC':
        results.sort(key=lambda g: g["latest_mtime_raw"])
    else:
        results.sort(key=lambda g: g["name"].lower())

    return results
