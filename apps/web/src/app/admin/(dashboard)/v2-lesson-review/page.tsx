"use client";

import V2AudioReviewQueue from "@/components/admin/V2AudioReviewQueue";

export default function V2LessonReviewPage({ embedded = false }: { embedded?: boolean } = {}) {
  return <V2AudioReviewQueue kind="lesson" embedded={embedded} />;
}
