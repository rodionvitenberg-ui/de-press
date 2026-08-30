import { useT } from "@/core/i18n/context";
import { useTheme, type ThemeMode } from "@/core/theme";
import styles from "./ThemeSwitch.module.css";

const modes: ThemeMode[] = ["auto", "dark", "light"];

export function ThemeSwitch() {
  const { mode, setMode } = useTheme();
  const t = useT();
  const labels: Record<ThemeMode, string> = {
    auto: t.theme.auto,
    dark: t.theme.dark,
    light: t.theme.light,
  };

  return (
    <div className={styles.group} role="group" aria-label={t.theme.label}>
      {modes.map((value) => (
        <button
          key={value}
          type="button"
          className={`${styles.button} ${
            mode === value ? styles.buttonActive : ""
          }`}
          aria-pressed={mode === value}
          onClick={() => setMode(value)}
        >
          {labels[value]}
        </button>
      ))}
    </div>
  );
}
