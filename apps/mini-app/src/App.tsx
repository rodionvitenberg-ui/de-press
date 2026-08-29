import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { FeedLayout } from "@/features/feed/FeedLayout";
import { StoryPage } from "@/features/feed/StoryPage";
import { StoryComposer } from "@/features/feed/StoryComposer";
import { ChatLayout } from "@/features/chat/ChatLayout";
import { DialoguePage } from "@/features/chat/DialoguePage";
import { NotificationsPane } from "@/features/notifications/NotificationsPane";
import { HelperQueue } from "@/features/helper/HelperQueue";
import { HelperJoin, HelperInviteCreate } from "@/features/helper/HelperJoin";
import { PatternsPane } from "@/features/patterns/PatternsPane";
import { HelpPane } from "@/features/help/HelpPane";
import { HelpWaitPane } from "@/features/help/HelpWaitPane";
import { CompanionPane } from "@/features/help/CompanionPane";
import { StartParamNavigator } from "@/core/host/StartParamNavigator";
import { TelegramBackButton } from "@/core/host/TelegramBackButton";
import { useI18n } from "@/core/i18n/context";
import styles from "./App.module.css";

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

        <Route path="/notifications" element={<NotificationsPane />} />
        <Route path="/patterns" element={<PatternsPane />} />
        <Route path="/help" element={<HelpPane />} />
        <Route path="/help/wait" element={<HelpWaitPane />} />
        <Route path="/help/ai" element={<CompanionPane />} />
        <Route path="/helper" element={<HelperQueue />} />
        <Route path="/helper/join" element={<HelperJoin />} />
        <Route path="/helper/invite" element={<HelperInviteCreate />} />

        <Route path="*" element={<EmptyPane text={t.shell.notFound} />} />
      </Route>
    </Routes>
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
