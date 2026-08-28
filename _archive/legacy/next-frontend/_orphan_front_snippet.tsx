"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError, API_URL } from "@/lib/api/client";
import type { ChatMessage, Dialogue } from "@/lib/types/api";
import { useChatSocket } from "@/hooks/useChatSocket";
import { useI18n } from "@/lib/i18n/context";
import { Button } from "@/components/ui/Button";
import { TextArea } from "@/components/ui/TextArea";
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

export function DialogueClient({ dialogueId }: Props) {
  const { locale, t } = useI18n();
  const [dialogue, setDialogue] = useState<Dialogue | null>(null);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [useHttpFallback, setUseHttpFallback] = useState(false);
  const [shownLang, setShownLang] = useState<Record<string, string>>({});

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
      <Link href="/me" className={styles.meta}>
        ← {t.nav.me}
      </Link>
      <p className={styles.meta}>
        {dialogueStatus}
        {dialogue ? ` · ${dialogue.intent}` : ""} · {statusLabel}
      </p>
      {dialogue?.rules ? <div className={styles.rules}>{dialogue.rules}</div> : null}
      {error || wsError ? (
        <p className={styles.error}>{error || wsError}</p>
      ) : null}
      {msg ? <p className={styles.meta}>{msg}</p> : null}

      <div className={styles.thread}>
        {messages.map((m) => {
          const audio = mediaUrl(m.audio_url);
          const isVoice = m.kind === "voice" || !!audio;
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
              {isVoice && m.duration_ms ? (
                <span className={styles.duration}>
                  {Math.max(1, Math.round(m.duration_ms / 1000))}s
                </span>
              ) : null}
              <div className={styles.msgActions}>
                {!m.is_system ? (
                  <button
                    type="button"
                    className={styles.msgAction}
                    onClick={() => void onTranslate(m.id)}
                  >
                    {t.chat.translate}
                  </button>
                ) : null}
                {!m.from_me && !m.is_system ? (
                  <button
                    type="button"
                    className={styles.msgAction}
                    onClick={() => void reportMsg(m.id)}
                  >
                    {t.report.report.toLowerCase()}
                  </button>
                ) : null}
              </div>
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
        <div className={styles.compose}>
          <TextArea
            id="msg"
            label={t.companion.label}
            value={body}
            onChange={(e) => onBodyChange(e.target.value)}
            onBlur={() => {
              if (!useHttpFallback && wsStatus === "open") setTyping(false);
            }}
            rows={3}
          />
          <div className={styles.actions}>
            <Button onClick={() => void send()} disabled={sending || !body.trim()}>
              {t.chat.send}
            </Button>
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
            />
            <Button variant="ghost" onClick={() => void close()}>
              {t.chat.close}
            </Button>
            <Button variant="danger" onClick={() => void blockPeer()}>
              {t.chat.hidePeer}
            </Button>
          </div>
        </div>
      ) : (
        <p className={styles.meta}>{t.chat.dialogueClosed}</p>
      )}
    </div>
  );
}