"""qBittorrent-side half of Oracle Cinema's archive-gated seed retention.

Runs on Ultra over Oracle's existing SSH key. Never logs torrent names or URLs.
"""

import base64
import hashlib
import http.cookiejar
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

HOME = pathlib.Path.home()
MEDIA = HOME / "media"
DOWNLOADS = HOME / "downloads"
API = "http://127.0.0.1:11491/api/v2/"
TRACKERS = {"tracker.torrentleech.org", "tracker.tleechreload.org"}
CATEGORIES = {"radarr", "tv-sonarr"}
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)


def api(path, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    request = urllib.request.Request(
        API + path, data=body, headers={"Referer": API}
    )
    with opener.open(request, timeout=25) as response:
        return response.read()


def authenticate():
    credentials = json.loads(
        (HOME / ".config/oracle-cinema/app-credentials.json").read_text()
    )
    response = api(
        "auth/login",
        {"username": "user9901231", "password": credentials["qbittorrent"]},
    )
    if response.strip() != b"Ok.":
        raise RuntimeError("qBittorrent authentication failed")


def torrent(hash_value):
    if not re.fullmatch(r"[a-fA-F0-9]{40,64}", hash_value):
        raise ValueError("Invalid torrent hash")
    matches = json.loads(api("torrents/info?hashes=" + hash_value))
    return next((item for item in matches if item["hash"] == hash_value), None)


def eligible_source(item, min_seed_days, min_idle_days):
    if item is None or item.get("category") not in CATEGORIES:
        return False
    host = urllib.parse.urlsplit(item.get("tracker", "")).hostname
    if host not in TRACKERS or item.get("progress", 0) < 1:
        return False
    if item.get("state") not in {"stalledUP", "uploading"}:
        return False
    tags = {tag.strip().lower() for tag in item.get("tags", "").split(",")}
    if tags & {"keep", "retain", "pinned", "no-prune"}:
        return False
    if item.get("upspeed", 0) or item.get("num_leechs", 0):
        return False
    if item.get("num_incomplete", -1) != 0:
        return False
    completed = item.get("completion_on", 0)
    last_activity = item.get("last_activity", 0)
    if completed <= 0 or last_activity <= 0:
        return False
    now = time.time()
    return (
        item.get("seeding_time", 0) >= min_seed_days * 86400
        and now - max(completed, last_activity) >= min_idle_days * 86400
        and now - completed >= min_seed_days * 86400
    )


def quota_bytes():
    result = subprocess.run(["quota", "-s"], capture_output=True, text=True, check=True)
    fields = result.stdout.strip().splitlines()[-1].split()
    def convert(raw):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)([KMGT]?)", raw.rstrip("*"))
        if not match:
            raise ValueError("Unexpected quota value")
        return round(float(match[1]) * 1024 ** ("KMGT".index(match[2]) + 1 if match[2] else 0))
    return {"used": convert(fields[1]), "limit": convert(fields[3])}


def snapshot():
    items = json.loads(api("torrents/info"))
    preferences = json.loads(api("app/preferences"))
    safe = []
    for item in items:
        if eligible_source(item, 14, 7):
            safe.append(
                {key: item.get(key) for key in
                 ("hash", "category", "size", "ratio", "seeding_time",
                  "last_activity", "completion_on", "num_incomplete")}
            )
    return {
        "quota": quota_bytes(),
        "torrentCount": len(items),
        "completedCount": sum(item.get("progress", 0) >= 1 for item in items),
        "maxActiveDownloads": preferences.get("max_active_downloads"),
        "ignoreSlowTorrents": preferences.get("dont_count_slow_torrents"),
        "candidateInputs": safe,
    }


def tracker_working(hash_value):
    trackers = json.loads(api("torrents/trackers?hash=" + hash_value))
    return any(
        tracker.get("status") == 2 and
        urllib.parse.urlsplit(tracker.get("url", "")).hostname in TRACKERS
        for tracker in trackers
    )


def describe(hash_value, min_seed_days, min_idle_days):
    item = torrent(hash_value)
    if not eligible_source(item, min_seed_days, min_idle_days):
        raise RuntimeError("Torrent is no longer eligible")
    if not tracker_working(hash_value):
        raise RuntimeError("Tracker is not reporting this seed as working")
    index = {}
    for library in (MEDIA / "Movies", MEDIA / "TV"):
        for base, _dirs, names in os.walk(library):
            for name in names:
                path = pathlib.Path(base) / name
                if path.is_symlink():
                    continue
                stat = path.stat()
                index.setdefault((stat.st_dev, stat.st_ino), []).append(path)
    mappings = []
    files = json.loads(api("torrents/files?hash=" + hash_value))
    if not files:
        raise RuntimeError("Torrent has no files")
    for entry in files:
        if entry.get("progress", 0) < 1:
            raise RuntimeError("Torrent has an incomplete file")
        downloaded = (pathlib.Path(item["save_path"]) / entry["name"]).resolve()
        if not downloaded.is_relative_to(DOWNLOADS.resolve()):
            raise RuntimeError("Torrent path is outside downloads")
        source_stat = downloaded.stat()
        matches = index.get((source_stat.st_dev, source_stat.st_ino), [])
        if len(matches) != 1 or source_stat.st_size != entry["size"]:
            raise RuntimeError("No unique imported hardlink for a torrent file")
        media_file = matches[0]
        mappings.append({
            "relative": media_file.relative_to(MEDIA).as_posix(),
            "size": source_stat.st_size,
            "inode": source_stat.st_ino,
            "device": source_stat.st_dev,
        })
    return {"files": mappings, "completionOn": item["completion_on"]}


def verified_paths(files):
    paths = []
    if not files:
        raise RuntimeError("Empty file list")
    for entry in files:
        original = MEDIA / entry["relative"]
        path = original.resolve()
        media_root = MEDIA.resolve()
        if not path.is_relative_to(media_root) or original.is_symlink():
            raise RuntimeError("Unsafe media path")
        if path.relative_to(media_root).parts[0] not in {"Movies", "TV"}:
            raise RuntimeError("Unmanaged media path")
        stat = path.stat()
        if (stat.st_size, stat.st_ino, stat.st_dev) != (
            entry["size"], entry["inode"], entry["device"]
        ):
            raise RuntimeError("Imported hardlink changed")
        paths.append(path)
    return paths


def hashes(files):
    output = []
    for path in verified_paths(files):
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        output.append(digest.hexdigest())
    return output


def retire(args):
    hash_value = args["hash"]
    if not eligible_source(torrent(hash_value), args["minSeedDays"], args["minIdleDays"]):
        raise RuntimeError("Torrent is no longer eligible")
    files = args["files"]
    paths = verified_paths(files)
    current = describe(hash_value, args["minSeedDays"], args["minIdleDays"])["files"]
    if current != files:
        raise RuntimeError("Torrent mapping changed")
    api("torrents/delete", {"hashes": hash_value, "deleteFiles": "true"})
    for _ in range(10):
        if torrent(hash_value) is None:
            break
        time.sleep(1)
    else:
        raise RuntimeError("qBittorrent did not remove the torrent")
    removed = 0
    for path, entry in zip(paths, files):
        stat = path.stat()
        if (stat.st_size, stat.st_ino, stat.st_dev) == (
            entry["size"], entry["inode"], entry["device"]
        ):
            path.unlink()
            removed += 1
    return {"retired": True, "mediaLinksRemoved": removed}


def set_download_limit(limit):
    if limit not in (0, 3):
        raise ValueError("Unsupported download limit")
    # Inactive/slow-torrent exemptions can bypass a zero download queue.
    api("app/setPreferences", {"json": json.dumps({
        "max_active_downloads": limit,
        "dont_count_slow_torrents": limit != 0,
    })})
    preferences = json.loads(api("app/preferences"))
    return {
        "maxActiveDownloads": preferences["max_active_downloads"],
        "ignoreSlowTorrents": preferences["dont_count_slow_torrents"],
    }


def main():
    operation = sys.argv[1]
    args = json.loads(base64.b64decode(sys.argv[2])) if len(sys.argv) > 2 else {}
    authenticate()
    if operation == "snapshot":
        result = snapshot()
    elif operation == "describe":
        result = describe(args["hash"], args["minSeedDays"], args["minIdleDays"])
    elif operation == "hashes":
        result = hashes(args["files"])
    elif operation == "retire":
        result = retire(args)
    elif operation == "set_download_limit":
        result = set_download_limit(args["limit"])
    else:
        raise ValueError("Unsupported operation")
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
