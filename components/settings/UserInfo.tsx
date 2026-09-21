import * as Application from "expo-application";
import { useAtom } from "jotai";
import { useTranslation } from "react-i18next";
import { Linking, View, type ViewProps } from "react-native";
import { APP_NAME } from "@/constants/Brand";
import { apiAtom, userAtom } from "@/providers/JellyfinProvider";
import { ListGroup } from "../list/ListGroup";
import { ListItem } from "../list/ListItem";

interface Props extends ViewProps {}

export const UserInfo: React.FC<Props> = ({ ...props }) => {
  const [api] = useAtom(apiAtom);
  const [user] = useAtom(userAtom);
  const { t } = useTranslation();

  const version =
    Application?.nativeApplicationVersion ||
    Application?.nativeBuildVersion ||
    "N/A";

  return (
    <View {...props}>
      <ListGroup title={t("home.settings.user_info.user_info_title")}>
        <ListItem
          title={t("home.settings.user_info.user")}
          value={user?.Name}
        />
        <ListItem
          title={t("home.settings.user_info.server")}
          value={api?.basePath}
        />
        <ListItem
          title={t("home.settings.user_info.app_version")}
          value={version}
        />
        <ListItem
          title={t("home.settings.user_info.source_code")}
          value={APP_NAME}
          onPress={() =>
            Linking.openURL("https://github.com/joshbilson/oracle-cinema")
          }
          showArrow
        />
        <ListItem
          title={t("home.settings.user_info.based_on")}
          value='Streamyfin · MPL-2.0'
          onPress={() =>
            Linking.openURL("https://github.com/streamyfin/streamyfin")
          }
          showArrow
        />
      </ListGroup>
    </View>
  );
};
