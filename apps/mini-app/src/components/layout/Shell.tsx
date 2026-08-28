import { Outlet } from "react-router-dom";
import { AntiPanicOverlay } from "@/features/anti-panic/AntiPanicOverlay";
import { useAntiPanic } from "@/core/hooks/useAntiPanic";
import { useNotifications } from "@/core/hooks/useNotifications";
import { Sidebar } from "./Sidebar";
import styles from "./Shell.module.css";

function LiveNotifications() {
  const { active } = useAntiPanic();
  // Anti-Panic kills sockets; don't reconnect while in panic mode
  useNotifications(!active);
  return null;
}

export function Shell() {
  return (
    <div className={styles.shell}>
      <a href="#main" className={styles.skip}>
        Skip
      </a>
      <Sidebar />
      <main id="main" className={styles.content}>
        <Outlet />
      </main>
      <AntiPanicOverlay />
      <LiveNotifications />
    </div>
  );
}
