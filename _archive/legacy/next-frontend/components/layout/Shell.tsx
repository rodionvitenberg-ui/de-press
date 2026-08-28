import type { ReactNode } from "react";
import { BottomNav } from "./BottomNav";
import { Footer } from "./Footer";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import styles from "./Shell.module.css";

interface ShellProps {
  children: ReactNode;
  narrow?: boolean;
}

export function Shell({ children, narrow = false }: ShellProps) {
  return (
    <div className={styles.shell}>
      <a href="#main" className={styles.skipLink}>
        К содержимому
      </a>
      <div className={styles.body}>
        <Sidebar />
        <div className={styles.right}>
          <Header />
          <main
            id="main"
            className={`${styles.main} ${narrow ? styles.mainNarrow : ""}`}
          >
            {children}
          </main>
          <Footer />
        </div>
      </div>
      <BottomNav />
    </div>
  );
}
