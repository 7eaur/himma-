import Link from "next/link";
import Image from "next/image";
import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.hero}>
      <div className={styles.heroContent}>
        {/* الشعار الأصلي من ملف SVG المعتمد */}
        <Image
          src="/brand/logo-gradient.svg"
          alt="شعار منصة هِمّة"
          width={160}
          height={80}
          priority
          className={styles.logo}
        />

        <h1 className={styles.title}>مرحباً بكم في منصة هِمّة</h1>
        <p className={styles.subtitle}>
          منصة تقييم مهارات القراءة العربية للمرحلة الابتدائية
        </p>

        <div className={styles.actions}>
          <Link href="/login?role=researcher" className="btn btn-primary">
            دخول الباحثة
          </Link>
          <Link href="/login?role=student" className="btn btn-secondary">
            دخول الطالب
          </Link>
        </div>
      </div>

      {/* شخصية الترحيب */}
      <div className={styles.characterWrap} aria-hidden="true">
        <Image
          src="/characters/boy-welcome.png"
          alt="شخصية هِمّة"
          width={280}
          height={280}
          className={styles.character}
          priority
        />
      </div>
    </main>
  );
}
