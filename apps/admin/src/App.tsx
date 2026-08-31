import { useState } from "react";
import { ApiError } from "./core/api/client";
import { useI18n } from "./core/i18n/context";
import { ModerationLog } from "./features/ModerationLog";
import { Overview } from "./features/Overview";
import { Reports } from "./features/Reports";

type Tab = "overview" | "reports" | "log";

export function App() {
  const { t, lang, setLang } = useI18n();
  const [tab, setTab] = useState<Tab>("overview");
  const [denied, setDenied] = useState(false);

  function onApiError(error: unknown) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      setDenied(true);
    }
  }

  if (denied) {
    return (
      <div className="screen">
        <main className="denied">
          <h1>{t.app.accessDenied}</h1>
          <p>{t.app.accessDeniedHint}</p>
          <a href="https://app.depress.co" className="btn">
            {t.app.openMainApp}
          </a>
        </main>
      </div>
    );
  }

  return (
    <div className="screen">
      <header className="top">
        <h1>{t.app.title}</h1>
        <nav className="tabs" aria-label="sections">
          {(
            [
              ["overview", t.app.tabOverview],
              ["reports", t.app.tabReports],
              ["log", t.app.tabLog],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              className={tab === key ? "tab tab-on" : "tab"}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </nav>
        <button
          type="button"
          className="tab"
          onClick={() => setLang(lang === "ru" ? "en" : "ru")}
        >
          {lang === "ru" ? "EN" : "RU"}
        </button>
      </header>
      <main>
        {tab === "overview" && <Overview onError={onApiError} />}
        {tab === "reports" && <Reports onError={onApiError} />}
        {tab === "log" && <ModerationLog onError={onApiError} />}
      </main>
    </div>
  );
}
