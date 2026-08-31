import { Outlet } from "react-router-dom";
import { AntiPanicOverlay } from "@/features/anti-panic/AntiPanicOverlay";
import { Sidebar } from "./Sidebar";
import styles from "./Shell.module.css";

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
    </div>
  );
}
