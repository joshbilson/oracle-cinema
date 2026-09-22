import { TouchableOpacity, View } from "react-native";
import { Text } from "@/components/common/Text";

type SearchType = "Library" | "Discover";
interface SearchTabButtonsProps {
  searchType: SearchType;
  setSearchType: (type: SearchType) => void;
  t: (key: string) => string;
}
export function SearchTabButtons({
  searchType,
  setSearchType,
  t,
}: SearchTabButtonsProps) {
  return (
    <View style={{ flexDirection: "row", gap: 8 }}>
      {(["Library", "Discover"] as const).map((type) => (
        <TouchableOpacity
          key={type}
          accessibilityRole='button'
          accessibilityState={{ selected: searchType === type }}
          onPress={() => setSearchType(type)}
          style={{
            paddingHorizontal: 16,
            paddingVertical: 12,
            borderRadius: 20,
            backgroundColor: searchType === type ? "#9333ea" : "#262626",
          }}
        >
          <Text>
            {t(type === "Library" ? "search.library" : "search.discover")}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}
