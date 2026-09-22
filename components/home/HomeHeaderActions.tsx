import { Stack } from "expo-router";
import { useAtomValue } from "jotai";
import { useTranslation } from "react-i18next";
import { useChromecastControls } from "@/components/Chromecast";
import { Colors } from "@/constants/Colors";
import useRouter from "@/hooks/useAppRouter";
import { useSessions } from "@/hooks/useSessions";
import { useDownload } from "@/providers/DownloadProvider";
import { userAtom } from "@/providers/JellyfinProvider";

export function HomeHeaderActions() {
  const router = useRouter();
  const { downloadedItems } = useDownload();
  const user = useAtomValue(userAtom);
  const { t } = useTranslation();
  const openCastControls = useChromecastControls();
  const { sessions = [] } = useSessions({
    refetchInterval: 5000,
    activeWithinSeconds: 360,
  });

  return (
    <>
      <Stack.Toolbar placement='left'>
        <Stack.Toolbar.Button
          icon='arrow.down.to.line'
          tintColor={downloadedItems.length ? Colors.primary : "white"}
          onPress={() => router.push("/(auth)/(tabs)/(home)/downloads")}
        >
          {t("home.downloads.downloads_title")}
        </Stack.Toolbar.Button>
      </Stack.Toolbar>
      <Stack.Toolbar placement='right'>
        <Stack.Toolbar.Button icon='airplay.video' onPress={openCastControls}>
          Cast
        </Stack.Toolbar.Button>
        {user?.Policy?.IsAdministrator && (
          <Stack.Toolbar.Button
            icon='play.circle'
            tintColor={sessions.length === 0 ? "white" : "#9333ea"}
            onPress={() => router.push("/(auth)/(tabs)/(home)/sessions")}
          >
            {t("home.sessions.title")}
          </Stack.Toolbar.Button>
        )}
        <Stack.Toolbar.Button
          icon='gearshape'
          onPress={() => router.push("/(auth)/(tabs)/(home)/settings")}
        >
          {t("home.settings.settings_title")}
        </Stack.Toolbar.Button>
      </Stack.Toolbar>
    </>
  );
}
