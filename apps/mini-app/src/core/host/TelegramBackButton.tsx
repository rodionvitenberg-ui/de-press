import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useHost } from "./HostContext";
import { parentPath } from "./navigation";
import { getTelegramWebApp } from "./telegram";

/**
 * Sync Telegram.WebApp.BackButton with React Router hierarchy.
 * Show on nested routes (/feed/:id, /chat/:id, …); hide on section roots.
 */
export function TelegramBackButton() {
  const { isTelegram, ready } = useHost();
  const location = useLocation();
  const navigate = useNavigate();
  const parent = parentPath(location.pathname);
  const show = Boolean(parent);

  useEffect(() => {
    if (!isTelegram || !ready) return;
    const wa = getTelegramWebApp();
    if (!wa?.BackButton) return;

    const onBack = () => {
      if (parent) {
        navigate(parent);
      } else {
        navigate(-1);
      }
    };

    try {
      if (show) {
        wa.BackButton.onClick(onBack);
        wa.BackButton.show();
      } else {
        wa.BackButton.hide();
      }
    } catch {
      /* older clients */
    }

    return () => {
      try {
        wa.BackButton.offClick(onBack);
        wa.BackButton.hide();
      } catch {
        /* ignore */
      }
    };
  }, [isTelegram, ready, show, parent, navigate, location.pathname]);

  return null;
}
