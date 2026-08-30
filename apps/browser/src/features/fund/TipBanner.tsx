import { useState } from "react";
import { useI18n } from "@/core/i18n/context";
import { USDC_MINT } from "./wallet";
import styles from "./fund.module.css";

/**
 * Thank-you tip banner for a closed help dialogue. Shown only when the
 * backend exposed the helper's opt-in `peer_tip_wallet` (closed dialogue,
 * grateful viewer) — the platform itself never touches the transfer.
 */
export function TipBanner({ wallet }: { wallet: string }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(wallet);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable — the wallet stays visible as text.
    }
  };

  return (
    <aside className={styles.banner}>
      <p className={styles.bannerTitle}>{t.fund.tipTitle}</p>
      <p className={styles.lead}>{t.fund.tipText}</p>
      <code className={styles.addr}>{wallet}</code>
      <div className={styles.row}>
        <button type="button" className={styles.btn} onClick={() => void copy()}>
          {copied ? t.fund.copied : t.fund.copy}
        </button>
        <a className={styles.btn} href={`solana:${wallet}?spl-token=${USDC_MINT}`}>
          {t.fund.donate}
        </a>
      </div>
    </aside>
  );
}