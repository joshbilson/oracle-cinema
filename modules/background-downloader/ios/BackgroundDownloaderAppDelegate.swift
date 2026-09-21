import ExpoModulesCore
import UIKit

public class BackgroundDownloaderAppDelegate: ExpoAppDelegateSubscriber {
  public func application(
    _ application: UIApplication,
    handleEventsForBackgroundURLSession identifier: String,
    completionHandler: @escaping () -> Void
  ) {
    if identifier == "\(Bundle.main.bundleIdentifier ?? "app.oracle.cinema").backgrounddownloader" {
      BackgroundDownloaderModule.setBackgroundCompletionHandler(completionHandler)
    }
  }
}

