# Seerr episode availability

Upstream: [seerr-team/seerr v3.4.1](https://github.com/seerr-team/seerr/tree/v3.4.1), commit `69f73a6f1486fdb51b8ddae9a94a8dfb629f461c`.

Jellyfin can return a newly added television item as an `Episode` or `Season`. Seerr 3.4.1 only dispatched `Series` items to its television scanner, so a downloaded episode could be playable while the request remained marked as processing. This patch sends all three item types through the existing series resolver and availability calculation.

The regression tests exercise a recent episode and a recent season through the scanner's public `run()` method and verify persisted partial availability, the parent show's Jellyfin ID and the season's status. Both failed before the fix. All five tests in the Jellyfin scanner test file passed afterward, and the server build passed.

Apply `seerr-3.4.1-episode-availability.patch` in a clean checkout of the pinned Seerr revision with `git apply --check`, then `git apply`. Run Seerr's scanner tests and server build before restarting its service. This is a server patch; it does not require rebuilding the iPhone app. Recheck whether upstream has incorporated the fix before upgrading Seerr.

The Seerr-derived patch and tests retain Seerr's MIT licence; see [SEERR-LICENSE](SEERR-LICENSE). The app's own licensing is documented separately in the repository root.
