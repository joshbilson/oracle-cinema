const { withAppDelegate, withInfoPlist } = require("expo/config-plugins");

// Expo SDK 56 uses the legacy window lifecycle. Xcode 27 requires scenes.
// Keep this migration local until the upstream app adopts Expo's scene support.
const sceneDelegate = `
#if os(iOS)
class OracleSceneDelegate: UIResponder, UIWindowSceneDelegate {
  var window: UIWindow?

  private var appDelegate: AppDelegate? {
    UIApplication.shared.delegate as? AppDelegate
  }

  func scene(
    _ scene: UIScene,
    willConnectTo session: UISceneSession,
    options connectionOptions: UIScene.ConnectionOptions
  ) {
    guard let windowScene = scene as? UIWindowScene,
          let appDelegate,
          let factory = appDelegate.reactNativeFactory else { return }

    let window = UIWindow(windowScene: windowScene)
    self.window = window
    appDelegate.window = window

    var launchOptions = appDelegate.oracleLaunchOptions ?? [:]
    if let context = connectionOptions.urlContexts.first {
      launchOptions[.url] = context.url
      if let source = context.options.sourceApplication {
        launchOptions[.sourceApplication] = source
      }
      launchOptions[.annotation] = context.options.annotation
    }
    if let activity = connectionOptions.userActivities.first {
      launchOptions[.userActivityDictionary] = [
        "UIApplicationLaunchOptionsUserActivityTypeKey": activity.activityType,
        "UIApplicationLaunchOptionsUserActivityKey": activity
      ]
    }
    factory.startReactNative(withModuleName: "main", in: window, launchOptions: launchOptions)
    appDelegate.oracleLaunchOptions = nil
  }

  func scene(_ scene: UIScene, openURLContexts contexts: Set<UIOpenURLContext>) {
    for context in contexts {
      var options: [UIApplication.OpenURLOptionsKey: Any] = [
        .openInPlace: context.options.openInPlace
      ]
      options[.sourceApplication] = context.options.sourceApplication
      options[.annotation] = context.options.annotation
      _ = appDelegate?.application(UIApplication.shared, open: context.url, options: options)
    }
  }

  func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
    _ = appDelegate?.application(UIApplication.shared, continue: userActivity, restorationHandler: { _ in })
  }

  // Expo SDK 56 subscribers still receive lifecycle events through AppDelegate.
  func sceneDidBecomeActive(_ scene: UIScene) {
    appDelegate?.applicationDidBecomeActive(UIApplication.shared)
  }

  func sceneWillResignActive(_ scene: UIScene) {
    appDelegate?.applicationWillResignActive(UIApplication.shared)
  }

  func sceneWillEnterForeground(_ scene: UIScene) {
    appDelegate?.applicationWillEnterForeground(UIApplication.shared)
  }

  func sceneDidEnterBackground(_ scene: UIScene) {
    appDelegate?.applicationDidEnterBackground(UIApplication.shared)
  }
}
#endif
`;

module.exports = function withOracleScenes(config) {
  if (process.env.EXPO_TV === "1") return config;

  config = withInfoPlist(config, (mod) => {
    mod.modResults.UIApplicationSceneManifest = {
      UIApplicationSupportsMultipleScenes: false,
      UISceneConfigurations: {
        UIWindowSceneSessionRoleApplication: [
          {
            UISceneConfigurationName: "Oracle Cinema",
            UISceneDelegateClassName:
              "$(PRODUCT_MODULE_NAME).OracleSceneDelegate",
          },
        ],
      },
    };
    return mod;
  });

  return withAppDelegate(config, (mod) => {
    let source = mod.modResults.contents;
    if (source.includes("class OracleSceneDelegate:")) return mod;
    if (mod.modResults.language !== "swift") {
      throw new Error(
        "Oracle Cinema scene support requires the Swift AppDelegate.",
      );
    }

    const legacyWindow =
      /#if os\(iOS\) \|\| os\(tvOS\)\s+window = UIWindow\(frame: UIScreen\.main\.bounds\)\s+factory\.startReactNative\(\s+withModuleName: "main",\s+in: window,\s+launchOptions: launchOptions\)\s+#endif/;
    if (!legacyWindow.test(source)) {
      throw new Error(
        "The Expo AppDelegate template changed; review the Oracle scene migration.",
      );
    }
    source = source.replace(
      "var window: UIWindow?",
      "var window: UIWindow?\n  var oracleLaunchOptions: [UIApplication.LaunchOptionsKey: Any]?",
    );
    source = source.replace(
      legacyWindow,
      "    oracleLaunchOptions = launchOptions",
    );
    mod.modResults.contents = source + sceneDelegate;
    return mod;
  });
};
