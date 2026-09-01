import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { FeedLayout } from "@/features/feed/FeedLayout";
import { StoryPage } from "@/features/feed/StoryPage";
import { StoryComposer } from "@/features/feed/StoryComposer";
import { ChatLayout } from "@/features/chat/ChatLayout";
import { DialoguePage } from "@/features/chat/DialoguePage";
import { StartParamNavigator } from "@/core/host/StartParamNavigator";
import { TelegramBackButton } from "@/core/host/TelegramBackButton";
import { useI18n } from "@/core/i18n/context";
import styles from "./App.module.css";

// Heavy, non-first-paint panes load on demand (audit Q4); feed and chat stay
// eager — they are the entry surfaces. Named exports need the default mapping.
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

function AppRoutes() {
  const { t } = useI18n();

  return (
    <Suspense fallback={<EmptyPane text="…" />}>
      <Routes>
      <Route element={<Shell />}>
        <Route path="/" element={<Navigate to="/feed" replace />} />

        {/* Nested: list stays mounted (TG desktop feel) */}
        <Route path="/feed" element={<FeedLayout />}>
          <Route index element={<EmptyPane text={t.shell.pickStory} />} />
          <Route path="new" element={<StoryComposer />} />
          <Route path=":id" element={<StoryPage />} />
        </Route>

        <Route path="/chat" element={<ChatLayout />}>
          <Route index element={<EmptyPane text={t.shell.pickChat} />} />
          <Route path=":id" element={<DialoguePage />} />
        </Route>

        <Route path="/patterns" element={<PatternsPane />} />
        <Route path="/therapy" element={<TherapyPane />} />
        <Route path="/help" element={<HelpPane />} />
        <Route path="/help/wait" element={<HelpWaitPane />} />
        <Route path="/help/ai" element={<CompanionPane />} />
        <Route path="/helper" element={<HelperQueue />} />
        <Route path="/helper/join" element={<HelperJoin />} />
        <Route path="/helper/invite" element={<HelperInviteCreate />} />

        <Route path="*" element={<EmptyPane text={t.shell.notFound} />} />
      </Route>
      </Routes>
    </Suspense>
  );
}

export function App() {
  return (
    <>
      <StartParamNavigator />
      <TelegramBackButton />
      <AppRoutes />
    </>
  );
}
