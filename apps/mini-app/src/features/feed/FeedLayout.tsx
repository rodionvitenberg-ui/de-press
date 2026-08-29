import { Outlet } from "react-router-dom";
import { ResizableSplit } from "@/components/tg/ResizableSplit";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useFeedSocket } from "@/core/hooks/useFeedSocket";
import { FeedLiveContext } from "./feedLiveContext";
import { FeedList } from "./FeedList";

/** Keeps yellow-zone FeedList mounted; list column is resizable. */
export function FeedLayout() {
  const { active: panic } = useAntiPanic();
  const live = useFeedSocket(!panic);
  return (
    <FeedLiveContext.Provider value={live}>
      <ResizableSplit list={<FeedList />} main={<Outlet />} />
    </FeedLiveContext.Provider>
  );
}
