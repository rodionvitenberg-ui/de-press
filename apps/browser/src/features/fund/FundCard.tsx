import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/core/api/client";
import { useI18n } from "@/core/i18n/context";
import { USDC_MINT } from "./wallet";
import styles from "./fund.module.css";

/** Public treasury block. Hidden while TREASURY_SOLANA_ADDRESS is unset. */
export function FundCard() {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const infoQuery = useQuery({
    queryKey: ["fund-info"],
    queryFn: () => api.fundInfo(),
    staleTime: 5 * 60_000,
  });
  const address = infoQuery.data?.treasury_address ?? "";
  if (!address) return null;
  const squads = infoQuery.data?.squads_url ?? "";
  const donateHref = `solana:${address}?spl-token=${USDC_MINT}`;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable (insecure context) — the address stays
      // visible and selectable as text.
    }
  };

  return (
    <section className={styles.card}>
      <h2 className={styles.cardTitle}>{t.fund.supportTitle}</h2>
      <p className={styles.lead}>{t.fund.supportText}</p>
      <code className={styles.addr}>
        {t.fund.treasuryLabel}: {address}
      </code>
      <div className={styles.row}>
        <button type="button" className={styles.btn} onClick={() => void copy()}>
          {copied ? t.fund.copied : t.fund.copy}
        </button>
        <a className={styles.btn} href={donateHref}>
          {t.fund.donate}
        </a>
        {squads ? (
          <a className={styles.btnLink} href={squads} target="_blank" rel="noreferrer">
            Squads
          </a>
        ) : null}
        <a
          className={styles.btnLink}
          href={`https://solscan.io/account/${address}`}
          target="_blank"
          rel="noreferrer"
        >
          Solscan
        </a>
      </div>
    </section>
  );
}