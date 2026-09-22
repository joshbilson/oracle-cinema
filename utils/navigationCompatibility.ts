import { Platform } from "react-native";
import { featureFlags } from "react-native-screens";

// Screens 4.25.2 can lose hit testing when a tab changes during a stack pop.
// Apply before Expo Router mounts any screens. Upstream issue: #4361.
if (Platform.OS === "ios") {
  featureFlags.experiment.ios26AllowInteractionsDuringTransition = false;
}
