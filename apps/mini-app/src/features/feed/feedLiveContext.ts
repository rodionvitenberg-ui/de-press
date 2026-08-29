import { createContext, useContext } from "react";
import type { FeedLiveStatus } from "@/core/hooks/useFeedSocket";

export const FeedLiveContext = createContext<{ status: FeedLiveStatus }>({
  status: "closed",
});

export function useFeedLive() {
  return useContext(FeedLiveContext);
}
