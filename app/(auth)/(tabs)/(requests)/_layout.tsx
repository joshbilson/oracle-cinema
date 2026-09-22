import { Stack } from "expo-router";
import { Platform } from "react-native";
import {
  commonScreenOptions,
  nestedTabPageScreenOptions,
} from "@/components/stacks/NestedTabPageStack";

export default function RequestsLayout() {
  return (
    <Stack>
      <Stack.Screen
        name='index'
        options={{
          headerShown: !Platform.isTV,
          headerTitle: "Requests",
          headerBlurEffect: "none",
          headerTransparent: Platform.OS === "ios",
          headerShadowVisible: false,
        }}
      />
      {Object.entries(nestedTabPageScreenOptions).map(([name, options]) => (
        <Stack.Screen key={name} name={name} options={options} />
      ))}
      <Stack.Screen
        name='collections/[collectionId]'
        options={{
          title: "",
          headerShown: !Platform.isTV,
          headerBlurEffect: "none",
          headerTransparent: Platform.OS === "ios",
          headerShadowVisible: false,
        }}
      />
      <Stack.Screen name='jellyseerr/page' options={commonScreenOptions} />
      <Stack.Screen
        name='jellyseerr/person/[personId]'
        options={commonScreenOptions}
      />
      <Stack.Screen
        name='jellyseerr/company/[companyId]'
        options={commonScreenOptions}
      />
      <Stack.Screen
        name='jellyseerr/genre/[genreId]'
        options={commonScreenOptions}
      />
    </Stack>
  );
}
