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

## Xcode 27 compatibility

This fork includes a CocoaPods deployment-target adjustment for older resource bundles, a small Expo Modules JSI patch preserving nullable C callbacks, and an iOS scene-lifecycle config plugin. The scene plugin keeps normal and universal links plus Expo lifecycle callbacks connected. These changes are applied by `bun install` and Expo prebuild; keep the pinned dependencies when rebuilding.

## Server

Connect to a Jellyfin server using HTTPS. Oracle's deployment uses private Tailscale HTTPS, so the device must be connected to the same tailnet. Movie and TV libraries live on Oracle, not on this Mac. Seerr and the Streamyfin companion plugin supply request discovery and login integration.

Requests run through Seerr on Oracle, with Radarr, Sonarr, Prowlarr and qBittorrent on the Ultra seedbox. Completed imports refresh Jellyfin. A read-only combined library prefers the Oracle archive and falls back to completed media on Ultra while the background copy runs. The default request quality profile permits 720p and 1080p.

Build 3 adds a permanent Requests tab with inline connection setup and searchable movie/TV discovery. Search uses regular React Native input controls with explicit keyboard dismissal. The installed react-native-screens 4.25.2 has an iOS stack-pop/tab-switch hit-testing regression (upstream issue #4361); `utils/navigationCompatibility.ts` disables its experimental iOS transition interactions before Expo Router mounts. Reassess that workaround when upgrading Screens. Seerr search terms are encoded centrally in the API client because Seerr validates the decoded query parameter as a URI-encoded value.

The Seerr 3.4.1 deployment includes the [episode availability patch](server-patches/README.md), which makes recent episode and season additions update request availability. Keep this patch when rebuilding that server version; do not apply it blindly to a newer release.

## Licence and credits

Streamyfin and this fork's covered source files are licensed under MPL-2.0. See `LICENSE.txt`. Original copyright and licence notices are preserved. When distributing this app outside the organisation, make the corresponding MPL-covered source, including modifications, available to recipients via the repository above. Third-party components retain their own licences and notices. The native video player includes GPL-3.0 MPVKit; its source and licence are available at https://github.com/mpv-ios/MPVKit/tree/0.41.0-av.

Oracle Cinema's name and original icon distinguish this personal fork from the upstream Streamyfin app. The vector icon can be regenerated with `swift scripts/oracle/generate-icon.swift`.

## Startup recovery (build 4)

The saved session is restored locally before server validation. Keychain migration and the current-user request must not keep the splash screen visible. Startup user validation has a ten-second timeout; the reachability probe resolves within eight seconds even if native fetch does not settle after cancellation.

Validated in the iOS 27 Release simulator using a local proxy that forwarded to Oracle and deliberately held `/Users/Me` and HEAD responses. Build 3 kept a black launch overlay visible. Build 4 exposed navigation, displayed Server Unreachable, allowed Settings to open, and recovered with Retry after the proxy resumed. Run `bun test utils/serverConnection.test.ts` for the bounded reachability checks.

### iOS 27 tab selection

`patches/react-native-bottom-tabs+1.2.0.patch` also backports [upstream #530](https://github.com/callstack/react-native-bottom-tabs/pull/530). iOS 27 SwiftUI tabs use `shouldSelectTab` instead of the prior view-controller delegate callback. Without this callback, native selection changes but React never mounts the selected tab. The backport retains the existing tvOS compilation fixes and maps tabs by identifier with an index fallback. The existing iOS 26 behavior is preserved. Reassess the patch when upgrading the pinned tab library.
