"use client";
import { useEffect } from "react";
import PlatformState from "@/components/PlatformState";
export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error("Page rendering error", error); }, [error]);
  return <PlatformState mode="error" onAction={reset} homeHref="/student" />;
}
