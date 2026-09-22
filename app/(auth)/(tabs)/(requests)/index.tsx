import { useEffect, useState } from "react";
import {
  Keyboard,
  ScrollView,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Text } from "@/components/common/Text";
import { JellyserrIndexPage } from "@/components/jellyseerr/JellyseerrIndexPage";
import { JellyseerrSettings } from "@/components/settings/Jellyseerr";
import { useJellyseerr } from "@/hooks/useJellyseerr";

export default function RequestsPage() {
  const { jellyseerrApi } = useJellyseerr();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setQuery(search.trim()), 250);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <ScrollView
      contentInsetAdjustmentBehavior='automatic'
      keyboardDismissMode='on-drag'
      keyboardShouldPersistTaps='handled'
      contentContainerStyle={{ paddingBottom: 60 }}
    >
      {!jellyseerrApi ? (
        <View style={{ padding: 20, gap: 16 }}>
          <Text style={{ fontSize: 22, fontWeight: "600" }}>
            Connect Requests
          </Text>
          <Text>
            Sign in with your Oracle Cinema account to request movies and TV
            shows. Keep Tailscale connected.
          </Text>
          <JellyseerrSettings />
        </View>
      ) : (
        <>
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
              margin: 16,
              gap: 8,
            }}
          >
            <TextInput
              accessibilityLabel='Search requests'
              placeholder='Search movies and TV shows'
              placeholderTextColor='#a3a3a3'
              value={search}
              onChangeText={setSearch}
              onSubmitEditing={() => {
                setQuery(search.trim());
                Keyboard.dismiss();
              }}
              returnKeyType='search'
              autoCorrect={false}
              clearButtonMode='while-editing'
              style={{
                flex: 1,
                minHeight: 48,
                borderRadius: 12,
                paddingHorizontal: 14,
                backgroundColor: "#262626",
                color: "white",
                fontSize: 16,
              }}
            />
            <TouchableOpacity
              accessibilityRole='button'
              accessibilityLabel='Dismiss keyboard'
              onPress={() => Keyboard.dismiss()}
              style={{ padding: 10 }}
            >
              <Text>Done</Text>
            </TouchableOpacity>
          </View>
          <JellyserrIndexPage searchQuery={query} />
        </>
      )}
    </ScrollView>
  );
}
