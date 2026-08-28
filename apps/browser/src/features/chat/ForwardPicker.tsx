import { useQuery } from "@tanstack/react-query";
import { api } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import styles from "./ForwardPicker.module.css";

interface ForwardPickerProps {
  currentId: string;
  onPick: (dialogueId: string) => void;
  onClose: () => void;
}

export function ForwardPicker({ currentId, onPick, onClose }: ForwardPickerProps) {
  const { t } = useI18n();
  const query = useQuery({
    queryKey: ["dialogues"],
    queryFn: () => api.myDialogues(),
  });
  const items = (query.data ?? []).filter(
    (d) =>
      d.id !== currentId &&
      d.status === "open" &&
      !d.hidden_for_me &&
      !d.can_reopen,
  );

  return (
    <div className={styles.backdrop} role="presentation" onClick={onClose}>
      <div
        className={styles.panel}
        role="dialog"
        aria-label={t.chat.forwardTitle}
        onClick={(e) => e.stopPropagation()}
      >
        <header className={styles.head}>
          <h2 className={styles.title}>{t.chat.forwardTitle}</h2>
          <button type="button" className={styles.x} onClick={onClose} aria-label={t.auth.closeMenu}>
            ×
          </button>
        </header>
        <div className={styles.list}>
          {items.length === 0 ? (
            <p className={styles.empty}>{t.chat.forwardEmpty}</p>
          ) : (
            items.map((d) => (
              <button
                key={d.id}
                type="button"
                className={styles.row}
                onClick={() => onPick(d.id)}
              >
                <strong>{d.peer_label || d.intent}</strong>
                <span>{d.last_preview || d.intent}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
