import { Platform } from "react-native";
import { Home } from "../../../../components/home/Home";

const HomeHeaderActions =
  Platform.OS === "ios" && !Platform.isTV
    ? require("@/components/home/HomeHeaderActions").HomeHeaderActions
    : null;

const Index = () => {
  return (
    <>
      {HomeHeaderActions && <HomeHeaderActions />}
      <Home />
    </>
  );
};

export default Index;
