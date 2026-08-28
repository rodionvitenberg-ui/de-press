import { Outlet } from "react-router-dom";
import { ResizableSplit } from "@/components/tg/ResizableSplit";
import { FeedList } from "./FeedList";

/** Keeps yellow-zone FeedList mounted; list column is resizable. */
export function FeedLayout() {
  return <ResizableSplit list={<FeedList />} main={<Outlet />} />;
}
