import { lazy, Suspense, useEffect, useRef } from "react";
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { recordRouteMs } from "@/core/perf";
import { useViewportMode } from "@/core/hooks/useViewportMode";
import type { ViewportMode } from "@/core/viewport";
import { Shell } from "@/components/layout/Shell";
import { AntiPanicOverlay } from "@/features/anti-panic/AntiPanicOverlay";
import { FeedLayout } from "@/features/feed/FeedLayout";
import { StoryPage } from "@/features/feed/StoryPage";
import { ChatLayout } from "@/features/chat/ChatLayout";
import { useI18n } from "@/core/i18n/context";
import styles from "./App.module.css";

const StoryComposer = lazy(() =>
  import("@/features/feed/StoryComposer").then((m) => ({
    default: m.StoryComposer,
  })),
);
const DialoguePage = lazy(() =>
  import("@/features/chat/DialoguePage").then((m) => ({
    default: m.DialoguePage,
  })),
);
const NotificationsPane = lazy(() =>
  import("@/features/notifications/NotificationsPane").then((m) => ({
    default: m.NotificationsPane,
  })),
);
const HelperQueue = lazy(() =>
  import("@/features/helper/HelperQueue").then((m) => ({
    default: m.HelperQueue,
  })),
);
const HelperJoin = lazy(() =>
  import("@/features/helper/HelperJoin").then((m) => ({
    default: m.HelperJoin,
  })),
);
const HelperInviteCreate = lazy(() =>
  import("@/features/helper/HelperJoin").then((m) => ({
    default: m.HelperInviteCreate,
  })),
);
const PatternsPane = lazy(() =>
  import("@/features/patterns/PatternsPane").then((m) => ({
    default: m.PatternsPane,
  })),
);
const TherapyPane = lazy(() =>
  import("@/features/therapy/TherapyPane").then((m) => ({
    default: m.TherapyPane,
  })),
);
const HelpPane = lazy(() =>
  import("@/features/help/HelpPane").then((m) => ({ default: m.HelpPane })),
);
const HelpWaitPane = lazy(() =>
  import("@/features/help/HelpWaitPane").then((m) => ({
    default: m.HelpWaitPane,
  })),
);
const CompanionPane = lazy(() =>
  import("@/features/help/CompanionPane").then((m) => ({
    default: m.CompanionPane,
  })),
);
const InboxPage = lazy(() =>
  import("@/features/inbox/InboxPage").then((m) => ({ default: m.InboxPage })),
);
const MorePane = lazy(() =>
  import("@/features/more/MorePane").then((m) => ({ default: m.MorePane })),
);

function EmptyPane({ text }: { text: string }) {
  return (
    <div className={styles.emptyPane}>
      <span className={styles.emptyMark} aria-hidden>
        ·
      </span>
      <p className={styles.emptyText}>{text}</p>
    </div>
  );
}

/**
 * Help journey runs full-bleed on desktop (no rail, whole page) while
 * phone/tablet keep the regular Shell with the TabBar. Anti-Panic overlay
 * stays available in both cases.
 */
function HelpChrome({ mode }: { mode: ViewportMode }) {
  if (mode !== "desktop") return <Shell />;
  return (
    <main id="main" className={styles.bare}>
      <Outlet />
      <AntiPanicOverlay />
    </main>
  );
}

function RoutePerf() {
  const location = useLocation();
  const started = useRef(performance.now());
  const lastPath = useRef(location.pathname);

  useEffect(() => {
    const path = location.pathname;
    if (path !== lastPath.current) {
      lastPath.current = path;
      started.current = performance.now();
    }
    const id = window.requestAnimationFrame(() => {
      recordRouteMs(path, performance.now() - started.current);
    });
    return () => window.cancelAnimationFrame(id);
  }, [location.pathname]);

  return null;
}

function AppRoutes({ mode }: { mode: ViewportMode }) {
  const { t } = useI18n();

  return (
    <Suspense fallback={<EmptyPane text={t.common.loading} />}>
      <Routes>
        <Route element={<HelpChrome mode={mode} />}>
          <Route path="/help" element={<HelpPane />} />
          <Route path="/help/wait" element={<HelpWaitPane />} />
          <Route path="/help/ai" element={<CompanionPane />} />
        </Route>
        <Route element={<Shell />}>
          <Route path="/" element={<Navigate to="/feed" replace />} />
          <Route path="/feed" element={<FeedLayout />}>
            <Route index element={<EmptyPane text={t.shell.pickStory} />} />
            <Route path="new" element={<StoryComposer />} />
            <Route path="mine" element={<EmptyPane text={t.feed.mine} />} />
            <Route path=":id" element={<StoryPage />} />
          </Route>
          <Route path="/chat" element={<ChatLayout />}>
            <Route index element={<EmptyPane text={t.shell.pickChat} />} />
            <Route path=":id" element={<DialoguePage />} />
          </Route>
          <Route path="/notifications" element={<NotificationsPane />} />
          <Route path="/patterns" element={<PatternsPane />} />
          <Route path="/therapy" element={<TherapyPane />} />
          <Route path="/helper" element={<HelperQueue />} />
          <Route path="/helper/join" element={<HelperJoin />} />
          <Route path="/helper/invite" element={<HelperInviteCreate />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/more" element={<MorePane />} />
          <Route path="*" element={<EmptyPane text={t.shell.notFound} />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

export function App() {
  const mode = useViewportMode();
  return (
    <>
      <RoutePerf />
      <AppRoutes mode={mode} />
    </>
  );
}
