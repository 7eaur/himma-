"use client";
import PlatformState from "@/components/PlatformState";
export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <PlatformState mode="error" onAction={reset} />;
}
