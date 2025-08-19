import styles from "./VoicePicker.module.css";

export default function VoicePicker({ voices = [], value, onChange, disabled }) {
  const list = voices.length ? voices : [{ shortName: "en-US-JennyNeural", locale: "en-US" }];
  return (
    <div className={styles.wrap} aria-disabled={disabled}>
      <span className={styles.label}>Voice</span>
      <select
        className={styles.select}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
      >
        {list.map(v => (
          <option key={v.shortName} value={v.shortName}>
            {v.shortName}
          </option>
        ))}
      </select>
    </div>
  );
}
