"""Keep valuable seeds while protecting Ultra quota and Oracle's archive.

This runs on Oracle after the independent rsync service. It never retires a
torrent unless all imported files match a completed Oracle archive byte for
byte. Tracker minimums are deliberately exceeded before a seed is eligible.
"""

import argparse
import base64
import hashlib
import json
import logging
import logging.handlers
import os
from pathlib import Path
import subprocess
import time

ROOT = Path("C:/media/meta/oracle-cinema")
ARCHIVE = Path("F:/Media")
STATUS = ROOT / "seedbox-retention-status.json"
SYNC_STATUS = ROOT / "seedbox-status.json"
REMOTE = "~/.config/oracle-cinema/ultra_retention_worker.py"
SSH_BIN = ROOT / "runtime/rsync/usr/bin/ssh.exe"
MAX_RETIRE_PER_PASS = 5


def thresholds(usage):
    """Return minimum active seed days, idle days, ratio and target use."""
    if usage >= 0.95:
        return (14, 7, 0.0, 0.85)
    if usage >= 0.90:
        return (21, 14, 0.0, 0.82)
    if usage >= 0.85:
        return (30, 21, 0.0, 0.78)
    if usage >= 0.75:
        return (45, 30, 1.0, 0.70)
    return None


def eligible(item, now, limits):
    seed_days, idle_days, ratio, _target = limits
    if item.get("ratio", 0) < ratio:
        return False
    if item.get("seeding_time", 0) < seed_days * 86400:
        return False
    completion = item.get("completion_on", 0)
    last_activity = item.get("last_activity", 0)
    return (
        completion > 0
        and last_activity > 0
        and now - completion >= seed_days * 86400
        and now - max(completion, last_activity) >= idle_days * 86400
    )


def ssh_call(operation, arguments=None, timeout=90):
    payload = base64.b64encode(json.dumps(arguments or {}).encode()).decode()
    command = [
        str(SSH_BIN), "-F", "/dev/null", "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3", "-o", "StrictHostKeyChecking=yes",
        "-o", "UserKnownHostsFile=/cygdrive/c/media/meta/oracle-cinema/private/ultra_known_hosts",
        "-i", "/cygdrive/c/media/meta/oracle-cinema/private/ultra_ed25519",
        "user9901231@tix.usbx.me",
        f"python3 {REMOTE} {operation} {payload}",
    ]
    env = os.environ.copy()
    env["PATH"] = str(SSH_BIN.parent) + ";" + env["PATH"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env)
    if result.returncode:
        raise RuntimeError(f"Ultra retention {operation} failed (exit {result.returncode})")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Ultra retention {operation} returned invalid data") from error


def archive_file(relative):
    parts = Path(relative).parts
    if not parts or parts[0] not in {"Movies", "TV"} or ".." in parts:
        raise RuntimeError("Unsafe archive path")
    path = ARCHIVE.joinpath(*parts)
    if not path.resolve().is_relative_to(ARCHIVE.resolve()) or path.is_symlink():
        raise RuntimeError("Unsafe archive link")
    return path


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def archive_verified(files):
    if not files:
        return False
    for entry in files:
        path = archive_file(entry["relative"])
        if not path.is_file() or path.stat().st_size != entry["size"]:
            return False
    remote_hashes = ssh_call("hashes", {"files": files}, timeout=1800)
    return all(
        digest(archive_file(entry["relative"])) == remote_hash
        for entry, remote_hash in zip(files, remote_hashes)
    ) and len(files) == len(remote_hashes)


def write_status(payload):
    payload["checkedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATUS.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2))
    temporary.replace(STATUS)


def run_once(dry_run=False):
    previous = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    inventory = ssh_call("snapshot")
    quota = inventory["quota"]
    usage = quota["used"] / quota["limit"]
    report = {
        "quotaUsedBytes": quota["used"], "quotaLimitBytes": quota["limit"],
        "quotaUsedPercent": round(usage * 100, 2),
        "torrentCount": inventory["torrentCount"],
        "completedCount": inventory["completedCount"],
        "eligibleCount": 0, "archiveVerifiedCount": 0,
        "retiredCount": 0,
        "downloadsHeld": previous.get("downloadsHeld", False) or (
            inventory["maxActiveDownloads"] == 0 and
            not inventory["ignoreSlowTorrents"]),
        "dryRun": dry_run, "error": None,
    }
    limits = thresholds(usage)
    if limits:
        now = time.time()
        items = [item for item in inventory["candidateInputs"] if eligible(item, now, limits)]
        items.sort(key=lambda item: (-item.get("ratio", 0), item["last_activity"]))
        report["eligibleCount"] = len(items)
        sync = json.loads(SYNC_STATUS.read_text()) if SYNC_STATUS.exists() else {}
        copied = sync.get("lastSuccessfulCopy", 0)
        if now - copied > 48 * 3600:
            report["error"] = "Oracle archive has not completed a copy in 48 hours"
            items = []
        for item in items[:MAX_RETIRE_PER_PASS]:
            args = {"hash": item["hash"], "minSeedDays": limits[0],
                    "minIdleDays": limits[1]}
            try:
                described = ssh_call("describe", args, timeout=180)
                if copied <= described["completionOn"]:
                    continue
                files = described["files"]
                if not archive_verified(files):
                    continue
                report["archiveVerifiedCount"] += 1
                if not dry_run:
                    outcome = ssh_call("retire", {**args, "files": files}, timeout=180)
                    if not outcome.get("retired") or outcome.get("mediaLinksRemoved") != len(files):
                        raise RuntimeError("A retired seed left an imported link behind")
                    report["retiredCount"] += 1
                    fresh = ssh_call("snapshot")
                    usage = fresh["quota"]["used"] / fresh["quota"]["limit"]
                    report["quotaUsedPercent"] = round(usage * 100, 2)
                    if usage <= limits[3]:
                        break
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                logging.warning("One candidate was protected: %s", type(error).__name__)
                report["error"] = "One candidate could not be verified; it was left seeding"
    if usage >= 0.90 and (not report["downloadsHeld"] or
                          inventory["maxActiveDownloads"] != 0 or
                          inventory["ignoreSlowTorrents"]):
        if not dry_run:
            result = ssh_call("set_download_limit", {"limit": 0})
            if result["maxActiveDownloads"] != 0 or result["ignoreSlowTorrents"]:
                raise RuntimeError("Could not hold new downloads")
        report["downloadsHeld"] = True
    elif usage < 0.80 and report["downloadsHeld"]:
        if not dry_run and (inventory["maxActiveDownloads"] != 3 or
                            not inventory["ignoreSlowTorrents"]):
            result = ssh_call("set_download_limit", {"limit": 3})
            if result["maxActiveDownloads"] != 3 or not result["ignoreSlowTorrents"]:
                raise RuntimeError("Could not resume downloads")
        report["downloadsHeld"] = False
    if not dry_run:
        write_status(report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    log = ROOT / "seedbox-retention.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(log, maxBytes=2_000_000, backupCount=3)
    logging.basicConfig(level=logging.INFO, handlers=[handler],
                        format="%(asctime)s %(levelname)s %(message)s")
    while True:
        try:
            report = run_once(args.dry_run)
            logging.info("Quota %.2f%%, eligible %d, archived %d, retired %d, held %s",
                         report["quotaUsedPercent"], report["eligibleCount"],
                         report["archiveVerifiedCount"], report["retiredCount"],
                         report["downloadsHeld"])
            if args.once:
                print(json.dumps(report))
                return
        except Exception as error:
            logging.error("Retention check failed: %s", type(error).__name__)
            if args.once:
                raise RuntimeError("Retention check failed") from error
            write_status({"error": type(error).__name__, "downloadsHeld":
                          json.loads(STATUS.read_text()).get("downloadsHeld", False)
                          if STATUS.exists() else False})
        time.sleep(3600)


if __name__ == "__main__":
    main()
