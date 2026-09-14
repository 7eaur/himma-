import Image from "next/image";
import styles from "./CanonicalRewardBadge.module.css";

export interface CanonicalRewardBadgeProps {
  label: string;
  assetPath: string;
  rewardKey?: string | null;
  variant?: "student" | "admin";
}

export default function CanonicalRewardBadge({
  label,
  assetPath,
  rewardKey,
  variant = "student",
}: CanonicalRewardBadgeProps) {
  return (
    <article
      className={`${styles.card} ${variant === "admin" ? styles.admin : styles.student}`}
      data-reward-key={rewardKey || undefined}
      data-testid="canonical-reward-badge"
    >
      <div className={styles.visual}>
        <Image src={assetPath} alt={`شارة ${label}`} width={118} height={118} />
      </div>
      <div className={styles.meta}>
        <strong>{label}</strong>
        <span>شارة مكتسبة</span>
      </div>
    </article>
  );
}
