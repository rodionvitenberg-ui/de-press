"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/Button";
import { TextInput } from "@/components/ui/TextArea";
import { useI18n } from "@/lib/i18n/context";
import styles from "./page.module.css";

export default function LoginPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(email, password);
      router.push("/feed");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : t.auth.loginErrorFallback,
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <h1 className={styles.title}>{t.auth.loginTitle}</h1>
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
        label={t.auth.password}
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error ? <p className={styles.error}>{error}</p> : null}
      <Button type="submit" disabled={loading}>
        {t.auth.submitLogin}
      </Button>
      <p className={styles.switch}>
        <Link href="/register">{t.auth.toRegister}</Link>
      </p>
    </form>
  );
}