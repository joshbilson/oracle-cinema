import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

HERE = Path(__file__).parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


retention = load("retention", "seedbox_retention.py")
worker = load("worker", "ultra_retention_worker.py")


class RetentionSafety(unittest.TestCase):
    def test_quota_hold_and_resume_keep_seeds_in_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            status = Path(directory) / "retention.json"
            sync = Path(directory) / "sync.json"
            sync.write_text(json.dumps({"lastSuccessfulCopy": time.time()}))
            calls = []
            quota_percent = 96
            download_limit = 3
            ignore_slow = True

            def fake_ssh(operation, arguments=None, timeout=90):
                nonlocal download_limit, ignore_slow
                calls.append(operation)
                if operation == "snapshot":
                    return {
                        "quota": {"used": quota_percent, "limit": 100},
                        "torrentCount": 9, "completedCount": 9,
                        "maxActiveDownloads": download_limit,
                        "ignoreSlowTorrents": ignore_slow,
                        "candidateInputs": [],
                    }
                self.assertEqual(operation, "set_download_limit")
                download_limit = arguments["limit"]
                ignore_slow = download_limit != 0
                return {"maxActiveDownloads": download_limit,
                        "ignoreSlowTorrents": ignore_slow}

            with mock.patch.object(retention, "STATUS", status), \
                 mock.patch.object(retention, "SYNC_STATUS", sync), \
                 mock.patch.object(retention, "ssh_call", side_effect=fake_ssh):
                held = retention.run_once()
                self.assertTrue(held["downloadsHeld"])
                self.assertEqual(held["retiredCount"], 0)
                self.assertEqual(calls, ["snapshot", "set_download_limit"])
                quota_percent = 79
                calls.clear()
                resumed = retention.run_once()
                self.assertFalse(resumed["downloadsHeld"])
                self.assertEqual(calls, ["snapshot", "set_download_limit"])

    def test_download_hold_disables_slow_torrent_exemption(self):
        for limit, ignore_slow in ((0, False), (3, True)):
            def fake_api(path, payload=None):
                if path == "app/setPreferences":
                    self.assertEqual(json.loads(payload["json"]), {
                        "max_active_downloads": limit,
                        "dont_count_slow_torrents": ignore_slow,
                    })
                    return b""
                self.assertEqual(path, "app/preferences")
                return json.dumps({
                    "max_active_downloads": limit,
                    "dont_count_slow_torrents": ignore_slow,
                }).encode()
            with mock.patch.object(worker, "api", side_effect=fake_api):
                self.assertEqual(worker.set_download_limit(limit), {
                    "maxActiveDownloads": limit,
                    "ignoreSlowTorrents": ignore_slow,
                })

    def test_pressure_never_shortens_tracker_margin_below_four_days(self):
        self.assertIsNone(retention.thresholds(0.74))
        self.assertEqual(retention.thresholds(0.76), (45, 30, 1.0, 0.70))
        self.assertEqual(retention.thresholds(0.91), (21, 14, 0.0, 0.82))
        self.assertEqual(retention.thresholds(0.96), (14, 7, 0.0, 0.85))

    def test_recent_activity_prevents_retirement_even_after_long_seeding(self):
        now = time.time()
        item = {"ratio": 2.0, "seeding_time": 60 * 86400,
                "completion_on": now - 60 * 86400,
                "last_activity": now - 86400}
        self.assertFalse(retention.eligible(item, now, retention.thresholds(0.96)))
        item["last_activity"] = now - 35 * 86400
        self.assertTrue(retention.eligible(item, now, retention.thresholds(0.76)))

    def test_private_unknown_and_active_seeds_cannot_be_removed(self):
        now = time.time()
        item = {"hash": "a" * 40, "category": "radarr",
                "tracker": "https://tracker.torrentleech.org/announce",
                "progress": 1, "state": "stalledUP", "tags": "",
                "upspeed": 0, "num_leechs": 0, "num_incomplete": 0,
                "completion_on": now - 40 * 86400,
                "last_activity": now - 35 * 86400,
                "seeding_time": 40 * 86400}
        self.assertTrue(worker.eligible_source(item, 14, 7))
        for change in ({"category": ""}, {"tracker": "https://other.example/announce"},
                       {"tags": "keep"}, {"upspeed": 1}, {"num_incomplete": 1},
                       {"state": "queuedUP"}, {"seeding_time": 9 * 86400}):
            candidate = {**item, **change}
            self.assertFalse(worker.eligible_source(candidate, 14, 7))
            with mock.patch.object(worker, "torrent", return_value=candidate), \
                 mock.patch.object(worker, "api") as api:
                with self.assertRaises(RuntimeError):
                    worker.retire({"hash": item["hash"], "minSeedDays": 14,
                                   "minIdleDays": 7, "files": []})
                api.assert_not_called()

    def test_unhealthy_tracker_prevents_archive_check_and_retirement(self):
        now = time.time()
        item = {"category": "radarr", "tracker": "https://tracker.torrentleech.org/announce",
                "progress": 1, "state": "stalledUP", "tags": "", "upspeed": 0,
                "num_leechs": 0, "num_incomplete": 0,
                "completion_on": now - 50 * 86400,
                "last_activity": now - 35 * 86400,
                "seeding_time": 50 * 86400}
        with mock.patch.object(worker, "torrent", return_value=item), \
             mock.patch.object(worker, "tracker_working", return_value=False), \
             mock.patch.object(worker, "api") as api:
            with self.assertRaisesRegex(RuntimeError, "Tracker is not reporting"):
                worker.describe("c" * 40, 14, 7)
            api.assert_not_called()

    def test_archive_mismatch_prevents_remote_hash_or_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(retention, "ARCHIVE", Path(directory)), \
                 mock.patch.object(retention, "ssh_call") as remote:
                path = Path(directory) / "Movies" / "test.bin"
                path.parent.mkdir()
                path.write_bytes(b"abc")
                self.assertFalse(retention.archive_verified(
                    [{"relative": "Movies/test.bin", "size": 4}]))
                remote.assert_not_called()
                with self.assertRaises(RuntimeError):
                    retention.archive_file("../private.bin")

    def test_retirement_removes_only_verified_seed_and_import_links(self):
        now = time.time()
        item = {"hash": "b" * 40, "category": "radarr",
                "tracker": "https://tracker.torrentleech.org/announce",
                "progress": 1, "state": "stalledUP", "tags": "",
                "upspeed": 0, "num_leechs": 0, "num_incomplete": 0,
                "completion_on": now - 50 * 86400,
                "last_activity": now - 35 * 86400,
                "seeding_time": 50 * 86400}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            download = root / "downloads" / "source.bin"
            imported = root / "media" / "Movies" / "source.bin"
            download.parent.mkdir()
            imported.parent.mkdir(parents=True)
            download.write_bytes(b"sample seed")
            imported.hardlink_to(download)
            stat = imported.stat()
            files = [{"relative": "Movies/source.bin", "size": stat.st_size,
                      "inode": stat.st_ino, "device": stat.st_dev}]

            def fake_api(path, payload=None):
                self.assertEqual(path, "torrents/delete")
                self.assertEqual(payload["deleteFiles"], "true")
                download.unlink()
                return b""

            with mock.patch.object(worker, "MEDIA", root / "media"), \
                 mock.patch.object(worker, "torrent", side_effect=[item, None]), \
                 mock.patch.object(worker, "tracker_working", return_value=True), \
                 mock.patch.object(worker, "describe", return_value={"files": files}), \
                 mock.patch.object(worker, "api", side_effect=fake_api):
                result = worker.retire({"hash": item["hash"], "minSeedDays": 14,
                                        "minIdleDays": 7, "files": files})
            self.assertEqual(result["mediaLinksRemoved"], 1)
            self.assertFalse(download.exists())
            self.assertFalse(imported.exists())


if __name__ == "__main__":
    unittest.main()
