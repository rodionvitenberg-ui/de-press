"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, API_URL } from "@/lib/api/client";
import type { ChatMessage, Dialogue } from "@/lib/types/api";
import { useChatSocket } from "@/hooks/useChatSocket";
import { useI18n } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { VoiceRecorder } from "@/components/dialogue/VoiceRecorder";
import styles from "./page.module.css";

interface Props {
  dialogueId: string;
}

function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_URL.replace(/\/$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function SendIcon() {
  return (
    <svg
      width={18}
      height={18}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg
      width={20}
      height={20}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </svg>
  );
}

function CircleIcon() {
  return (
    <svg
      width={20}
      height={20}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9" />
      <path d="m10 9 5 3-5 3V9Z" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function DialogueClient({ dialogueId }: Props) {
  const { locale, t } = useI18n();
  const [dialogue, setDialogue] = useState<Dialogue | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [useHttpFallback, setUseHttpFallback] = useState(false);
  const [shownLang, setShownLang] = useState<Record<string, string>>({});
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const {
    status: wsStatus,
    messages,
    setMessages,
    dialogueStatus,
    setDialogueStatus,
    peerTyping,
    setTyping,
    reconnectAttempt,
    error: wsError,
    send: wsSend,
    closeDialogue: wsClose,
  } = useChatSocket(dialogueId, !useHttpFallback);

  const loadMeta = useCallback(async () => {
    try {
      const list = await api.myDialogues();
      const d = list.find((x) => x.id === dialogueId) ?? null;
      setDialogue(d);
      if (d) setDialogueStatus(d.status);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }, [dialogueId, setDialogueStatus, t.common.error]);

  useEffect(() => {
    void loadMeta();
  }, [loadMeta]);

  useEffect(() => {
    if (wsStatus === "error") {
      setUseHttpFallback(true);
      void (async () => {
        try {
          const msgs = await api.dialogueMessages(dialogueId);
          setMessages(msgs);
        } catch {
          /* ignore */
        }
      })();
    }
  }, [wsStatus, dialogueId, setMessages]);

  useEffect(() => {
    if (!useHttpFallback) return;
    const timer = window.setInterval(async () => {
      try {
        const msgs = await api.dialogueMessages(dialogueId);
        setMessages(msgs);
      } catch {
        /* ignore */
      }
    }, 4000);
    return () => window.clearInterval(timer);
  }, [useHttpFallback, dialogueId, setMessages]);

  // Close the ⋯ menu on outside click / Escape.
  useEffect(() => {
    if (!menuOpen) return;
    const onClick = (ev: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(ev.target as Node)) {
        setMenuOpen(false);
      }
    };
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  function onBodyChange(value: string) {
    setBody(value);
    if (!useHttpFallback && wsStatus === "open") {
      setTyping(value.trim().length > 0);
    }
  }

  function upsertMessage(m: ChatMessage) {
    setMessages((prev: ChatMessage[]) =>
      prev.some((x) => x.id === m.id)
        ? prev.map((x) => (x.id === m.id ? { ...x, ...m } : x))
        : [...prev, m],
    );
  }

  async function send() {
    setSending(true);
    setError(null);
    try {
      if (!useHttpFallback && wsStatus === "open") {
        setTyping(false);
        wsSend(body);
        setBody("");
      } else {
        const m = await api.sendMessage(dialogueId, body, locale);
        upsertMessage(m);
        setBody("");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setSending(false);
    }
  }

  async function sendVoice(blob: Blob, durationMs: number) {
    setSending(true);
    setError(null);
    try {
      const m = await api.sendVoiceMessage(dialogueId, blob, {
        durationMs,
        sourceLang: locale,
        filename: "note.webm",
      });
      upsertMessage(m);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    } finally {
      setSending(false);
    }
  }

  async function close() {
    setMenuOpen(false);
    try {
      if (!useHttpFallback && wsStatus === "open") {
        setTyping(false);
        wsClose();
        setDialogueStatus("closed");
      } else {
        const d = await api.closeDialogue(dialogueId);
        setDialogue(d);
        setDialogueStatus(d.status);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }

  async function blockPeer() {
    setMenuOpen(false);
    if (!window.confirm(t.chat.hidePeerConfirm)) {
      return;
    }
    try {
      const res = await api.blockPeerInDialogue(dialogueId);
      setMsg(res.message);
      await close();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }

  async function reportMsg(messageId: string) {
    try {
      const res = await api.reportMessage(messageId, "abuse");
      setMsg(res.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }

  async function onTranslate(messageId: string) {
    try {
      const existing = messages.find((x) => x.id === messageId);
      const source = (existing?.source_lang || "ru").slice(0, 2);
      const ui = locale.slice(0, 2);
      // Prefer UI language; if already same as source, offer the other.
      const target = source === ui ? (ui === "en" ? "ru" : "en") : ui;
      const m = await api.translateMessage(messageId, target);
      upsertMessage(m);
      setShownLang((prev) => ({ ...prev, [messageId]: target }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t.common.error);
    }
  }

  function messageText(m: ChatMessage): string {
    const lang = shownLang[m.id];
    if (lang && m.translations?.[lang]) return m.translations[lang];
    if (m.display_text) return m.display_text;
    if (m.transcript) return m.transcript;
    return m.body;
  }

  const open = dialogueStatus === "open";
  const canSend = body.trim().length > 0;
  const statusLabel = useHttpFallback
    ? "HTTP"
    : wsStatus === "open"
      ? t.chat.statusLive
      : wsStatus === "connecting" && reconnectAttempt > 0
        ? t.chat.statusReconnect(reconnectAttempt)
        : wsStatus === "connecting"
          ? t.chat.statusConnecting
          : wsStatus === "closed"
            ? t.chat.statusClosed
            : t.chat.statusError;

  return (
    <div className={styles.page}>
      {dialogue?.rules ? <div className={styles.rules}>{dialogue.rules}</div> : null}
      {error || wsError ? (
        <p className={styles.error}>{error || wsError}</p>
      ) : null}
      {msg ? <p className={styles.meta}>{msg}</p> : null}

      <header className={styles.chatHeader}>
        <Link href="/me" className={styles.backLink} aria-label={t.chat.menuLabel}>
          ← {t.nav.me}
        </Link>
        <div className={styles.chatMeta}>
          <p className={styles.chatTitle}>
            {dialogue ? dialogue.intent : "…"}
          </p>
          <p className={styles.chatSub}>
            {dialogueStatus} · {statusLabel}
          </p>
        </div>
        <div className={styles.menuWrap} ref={menuRef}>
          <button
            type="button"
            className={styles.menuBtn}
            aria-label={t.chat.menuLabel}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <svg
              width={20}
              height={20}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              aria-hidden
            >
              <circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none" />
              <circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none" />
              <circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none" />
            </svg>
          </button>
          {menuOpen ? (
            <div className={styles.menu} role="menu" aria-label={t.chat.menuLabel}>
              <button
                type="button"
                role="menuitem"
                className={styles.menuItem}
                onClick={() => void close()}
              >
                {t.chat.menuClose}
              </button>
              <button
                type="button"
                role="menuitem"
                className={styles.menuItemDanger}
                onClick={() => void blockPeer()}
              >
                {t.chat.menuHide}
              </button>
            </div>
          ) : null}
        </div>
      </header>

      <div className={styles.thread}>
        {messages.map((m) => {
          const audio = mediaUrl(m.audio_url);
          const isVoice = m.kind === "voice" || !!audio;
          const time = formatTime(m.created_at);
          return (
            <div
              key={m.id}
              className={`${styles.msg} ${
                m.is_system ? styles.system : m.from_me ? styles.me : styles.them
              }`}
            >
              {isVoice && audio ? (
                <audio className={styles.audio} controls src={audio} preload="metadata" />
              ) : null}
              <div className={styles.msgBody}>{messageText(m)}</div>
              {!m.is_system ? (
                <div className={styles.msgMeta}>
                  {time ? <span className={styles.msgTime}>{time}</span> : null}
                  {isVoice && m.duration_ms ? (
                    <span className={styles.msgTime}>
                      {Math.max(1, Math.round(m.duration_ms / 1000))}s
                    </span>
                  ) : null}
                </div>
              ) : null}
              {!m.is_system ? (
                <div className={styles.msgActions}>
                  <button
                    type="button"
                    className={styles.msgAction}
                    onClick={() => void onTranslate(m.id)}
                  >
                    {t.chat.translate}
                  </button>
                  {!m.from_me ? (
                    <button
                      type="button"
                      className={styles.msgAction}
                      onClick={() => void reportMsg(m.id)}
                    >
                      {t.report.report.toLowerCase()}
                    </button>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}
        {peerTyping ? (
          <div className={styles.typing} aria-live="polite">
            <span className={styles.dots} aria-hidden>
              <i />
              <i />
              <i />
            </span>
            {t.chat.typing}
          </div>
        ) : null}
      </div>

      {open ? (
        <div className={styles.composer}>
          <button
            type="button"
            className={styles.composerBtn}
            aria-label={t.chat.circleAria}
            title={`${t.chat.circleAria} — ${t.chat.comingSoon}`}
            disabled
          >
            <CircleIcon />
          </button>
          <div className={styles.composerInput}>
            <textarea
              className={styles.composerTextarea}
              value={body}
              onChange={(e) => onBodyChange(e.target.value)}
              onBlur={() => {
                if (!useHttpFallback && wsStatus === "open") setTyping(false);
              }}
              rows={1}
              placeholder={t.chat.composerPlaceholder}
              aria-label={t.chat.composerPlaceholder}
            />
          </div>
          <VoiceRecorder
            disabled={sending}
            onRecorded={sendVoice}
            labels={{
              record: t.chat.record,
              stop: t.chat.stop,
              cancel: t.common.cancel,
              unsupported: t.chat.unsupported,
              recording: t.chat.recording,
            }}
            className={styles.composerBtn}
          />
          {canSend ? (
            <button
              type="button"
              className={`${styles.composerBtn} ${styles.sendBtn}`}
              onClick={() => void send()}
              disabled={sending}
              aria-label={t.chat.sendAria}
              title={t.chat.send}
            >
              <SendIcon />
            </button>
          ) : null}
        </div>
      ) : (
        <p className={styles.meta}>{t.chat.dialogueClosed}</p>
      )}
    </div>
  );
}