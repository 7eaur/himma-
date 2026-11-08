import styles from "./DeveloperCredit.module.css";

export default function DeveloperCredit() {
  return (
    <div className={styles.credit} dir="rtl" data-testid="developer-credit">
      <span>المطور:</span>
      <a href="https://wasl-tech.com" target="_blank" rel="noopener noreferrer">وصل تك</a>
    </div>
  );
}
