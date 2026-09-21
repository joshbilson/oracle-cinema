module.exports = ({ config }) => {
  if (process.env.EXPO_TV !== "1") {
    config.plugins.push("expo-background-task");

    config.plugins.push([
      "react-native-google-cast",
      { useDefaultExpandedMediaControls: true },
    ]);

    config.plugins.push([
      "expo-camera",
      {
        cameraPermission:
          "Allow Oracle Cinema to access the camera to scan QR codes for TV login.",
      },
    ]);
  }

  // Only override googleServicesFile if env var is set
  const androidConfig = {};
  if (process.env.GOOGLE_SERVICES_JSON) {
    androidConfig.googleServicesFile = process.env.GOOGLE_SERVICES_JSON;
  }

  config.ios.appleTeamId = process.env.ORACLE_APPLE_TEAM_ID || undefined;

  return {
    ...(Object.keys(androidConfig).length > 0 && { android: androidConfig }),
    ...config,
  };
};
