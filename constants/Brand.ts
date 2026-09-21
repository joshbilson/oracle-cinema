import Constants from "expo-constants";

export const APP_NAME = "Oracle Cinema";
export const APP_VERSION = Constants.expoConfig?.version ?? "1.0.0";

// Build-time defaults are public addresses, never passwords or API tokens.
// Keep the actual deployment values in the ignored .env.local file.
export const DEFAULT_SERVER_URL =
  process.env.EXPO_PUBLIC_ORACLE_SERVER_URL?.trim() ?? "";
