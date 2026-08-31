import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import { isValidSolanaAddress, signTipWalletChallenge } from "./wallet";
import styles from "./fund.module.css";

interface SavePayload {
  address: string;
  nonce?: string;
  signature?: string;
}

/** Helper-only opt-in: publish (or clear) a personal Solana tip address. */
export function TipWalletForm({
  current,
  verified = false,
}: {
  current: string;
  verified?: boolean;
}) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [address, setAddress] = useState("");
  const [localError, setLocalError] = useState("");

  const save = useMutation({
    mutationFn: (payload: SavePayload) => api.setTipWallet(payload),
    onSuccess: () => {
      setAddress("");
      setLocalError("");
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
    onError: (err) => {
      setLocalError(
        err instanceof ApiError ? err.message : t.common.error,
      );
    },
  });

  const submit = () => {
    const value = address.trim();
    if (value && !isValidSolanaAddress(value)) {
      setLocalError(t.fund.invalidAddress);
      return;
    }
    if (!value) {
      save.mutate({ address: "" });
      return;
    }
    // ADR-0020 phase 2: when an injected Solana wallet is present, attach an
    // ownership signature; without one (no wallet / user declined) the address
    // is saved unverified.
    void signTipWalletChallenge(value)
      .then((proof) =>
        save.mutate({
          address: value,
          nonce: proof.nonce,
          signature: proof.signature,
        }),
      )
      .catch(() => save.mutate({ address: value }));
  };

  return (
    <form
      className={styles.card}
      onSubmit={(ev) => {
        ev.preventDefault();
        submit();
      }}
    >
      <h2 className={styles.cardTitle}>{t.fund.tipWalletTitle}</h2>
      <p className={styles.lead}>{t.fund.tipWalletText}</p>
      {current ? (
        <p className={styles.current}>
          {t.fund.tipWalletCurrent}: <code>{current}</code>{" "}
          {verified ? (
            <span className={styles.badge}>{t.fund.verifiedBadge}</span>
          ) : null}
        </p>
      ) : null}
      <input
        className={styles.input}
        value={address}
        onChange={(e) => {
          setAddress(e.target.value);
          setLocalError("");
        }}
        placeholder={t.fund.tipWalletPlaceholder}
        spellCheck={false}
        autoComplete="off"
      />
      {localError ? <p className={styles.error}>{localError}</p> : null}
      <p className={styles.warn}>{t.fund.tipWalletWarn}</p>
      <div className={styles.row}>
        <button type="submit" className={styles.btn} disabled={save.isPending}>
          {t.common.save}
        </button>
        {current ? (
          <button
            type="button"
            className={styles.btn}
            disabled={save.isPending}
            onClick={() => save.mutate({ address: "" })}
          >
            {t.fund.clear}
          </button>
        ) : null}
      </div>
    </form>
  );
}
