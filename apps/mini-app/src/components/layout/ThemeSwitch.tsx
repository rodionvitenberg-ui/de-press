import { useTheme, type ThemeMode } from "@/core/theme";
import styles from "./ThemeSwitch.module.css";

const options: { value: ThemeMode; label: string }[] = [
  { value: "auto", label: "Авто" },
  { value: "dark", label: "Тёмная" },
  { value: "light", label: "Светлая" },
];

export function ThemeSwitch() {
  const { mode, setMode } = useTheme();

  return (
    <div className={styles.group} role="group" aria-label="Тема">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`${styles.button} ${
            mode === opt.value ? styles.buttonActive : ""
          }`}
          aria-pressed={mode === opt.value}
          onClick={() => setMode(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
