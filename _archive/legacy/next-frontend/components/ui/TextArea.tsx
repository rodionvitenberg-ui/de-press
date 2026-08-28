import type { TextareaHTMLAttributes } from "react";
import styles from "./TextArea.module.css";

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function TextArea({ label, id, className = "", ...rest }: TextAreaProps) {
  return (
    <label className={styles.field} htmlFor={id}>
      {label ? <span className={styles.label}>{label}</span> : null}
      <textarea id={id} className={`${styles.textarea} ${className}`} {...rest} />
    </label>
  );
}

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function TextInput({ label, id, className = "", ...rest }: TextInputProps) {
  return (
    <label className={styles.field} htmlFor={id}>
      {label ? <span className={styles.label}>{label}</span> : null}
      <input id={id} className={`${styles.input} ${className}`} {...rest} />
    </label>
  );
}
