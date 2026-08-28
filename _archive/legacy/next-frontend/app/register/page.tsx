"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextArea";
import { useI18n } from "@/lib/i18n/context";
import styles from "../login/page.module.css";

export default function RegisterPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pseudonym, setPseudonym] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.register(email, password, pseudonym);
      router.push("/feed");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : t.auth.registerErrorFallback,
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <h1 className={styles.title}>{t.auth.registerTitle}</h1>
      <p className={styles.msg}>{t.auth.registerOptional}</p>
      <TextInput
        id="email"
        label={t.auth.email}
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <TextInput
        id="password"
        label={t.auth.passwordMin}
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
      />
      <TextInput
        id="pseudonym"
        label={t.auth.pseudonym}
        value={pseudonym}
        onChange={(e) => setPseudonym(e.target.value)}
        placeholder={t.auth.pseudonymPlaceholder}
      />
      {error ? <p className={styles.error}>{error}</p> : null}
      <Button type="submit" disabled={loading}>
        {t.auth.submitRegister}
      </Button>
      <p className={styles.switch}>
        <Link href="/login">{t.auth.toLogin}</Link>
      </p>
    </form>
  );
}