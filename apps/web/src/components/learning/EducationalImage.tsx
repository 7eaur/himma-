"use client";

import Image from "next/image";
import { useState } from "react";
import styles from "./EducationalImage.module.css";

interface Props {
  src: string;
  alt: string;
  width: number;
  height: number;
  className?: string;
  onLoad?: () => void;
  onError: () => void;
}

/** Keep a quiet, transparent placeholder in the image's reserved space.
 * The caller keys by src, so an old load cannot reveal a new question's image.
 * Authenticated images must bypass Next's headerless image optimizer.
 */
export default function EducationalImage({ src, alt, width, height, className, onLoad, onError }: Props) {
  const [loaded, setLoaded] = useState(false);
  return <span className={styles.frame} aria-busy={!loaded}>
    {!loaded && <span className={styles.placeholder} role="status" aria-label="جاري تحميل الصورة">
      <svg viewBox="0 0 64 64" fill="none" aria-hidden="true">
        <rect x="7" y="9" width="50" height="46" rx="10" stroke="currentColor" strokeWidth="2"/>
        <circle cx="24" cy="24" r="5" fill="currentColor"/>
        <path d="m12 47 13-12 9 8 8-7 10 11" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </span>}
    <Image src={src} alt={alt} width={width} height={height} unoptimized
      loading="eager" decoding="async" className={className}
      style={{ opacity: loaded ? 1 : 0 }}
      onLoad={() => { setLoaded(true); onLoad?.(); }} onError={onError}/>
  </span>;
}
