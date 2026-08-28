import { Outlet } from "react-router-dom";
import { ResizableSplit } from "@/components/tg/ResizableSplit";
import { ChatList } from "./ChatList";

/** Keeps yellow-zone ChatList mounted; list column is resizable. */
export function ChatLayout() {
  return <ResizableSplit list={<ChatList />} main={<Outlet />} />;
}
