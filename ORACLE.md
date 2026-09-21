# Oracle Cinema

Personal movie and television app based on Streamyfin v0.54.1 (`46bd2a784e206f94a5e3eb2e24f0de570341f00e`).

- App name: Oracle Cinema
- iOS / Android application identifier: `app.oracle.cinema`
- URL scheme: `oraclecinema`
- Source: https://github.com/joshbilson/oracle-cinema
- Upstream: https://github.com/streamyfin/streamyfin

## Local build

Use Bun. The Jellyseerr type submodule is pinned to its recorded commit.

1. Copy `.env.example` to `.env.local` and set your server address and Apple signing team.
2. Run `bun install --frozen-lockfile` and `git submodule update --init --recursive`.
3. Run `EXPO_TV=0 bunx expo prebuild --platform ios`.
4. Build and archive the generated Xcode workspace using your own developer account.
5. Upload the archive to this app's own App Store Connect record for internal TestFlight testing.

The default server address is compiled into the app, but contains no credentials. Users authenticate normally. Keep `.env.local`, signing material, server backups, service settings and build exports out of Git. Build numbers must increase for each TestFlight upload.

The fork has no upstream Expo update URL, publishing identity or push project ID. Remote push registration is enabled only when our own Expo project is configured. Local download notifications remain supported.

## Server

Connect to a Jellyfin server using HTTPS. Oracle's deployment uses private Tailscale HTTPS, so the device must be connected to the same tailnet. Movie and TV libraries live on Oracle, not on this Mac. Seerr and the Streamyfin companion plugin supply request discovery and login integration.

## Licence and credits

Streamyfin and this fork's covered source files are licensed under MPL-2.0. See `LICENSE.txt`. Original copyright and licence notices are preserved. When distributing this app outside the organisation, make the corresponding MPL-covered source, including modifications, available to recipients via the repository above. Third-party components retain their own licences and notices. The native video player includes GPL-3.0 MPVKit; its source and licence are available at https://github.com/mpv-ios/MPVKit/tree/0.41.0-av.

Oracle Cinema's name and original icon distinguish this personal fork from the upstream Streamyfin app. The vector icon can be regenerated with `swift scripts/oracle/generate-icon.swift`.
