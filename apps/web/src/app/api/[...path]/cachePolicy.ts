const PRIVATE_NO_STORE = "private, no-store";
const APPROVED_MEDIA_PREFIX = "media/";

/**
 * Shared-cache boundary for the Next.js BFF.
 * Only successful read-only approved-media responses may be public.
 * Authentication state and every other API response remain private/no-store.
 */
export function responseCacheControl({
  upstreamPath,
  method,
  ok,
  upstreamCacheControl,
  hasSetCookie,
}: {
  upstreamPath: string;
  method: string;
  ok: boolean;
  upstreamCacheControl: string | null;
  hasSetCookie: boolean;
}): string {
  const educationalMediaRead = (
    /^v2\/content\/media\/[A-Z0-9-]+$/.test(upstreamPath)
    || /^v2\/lessons\/sessions\/[1-9]\d*\/media\/[A-Z0-9-]+$/.test(upstreamPath)
  ) && ["GET", "HEAD"].includes(method);
  // The authenticated API issues this exact browser-only policy exclusively
  // for fingerprinted educational images and videos. No response may enter shared caches.
  if (educationalMediaRead && ok && !hasSetCookie
    && upstreamCacheControl === "private, max-age=86400, immutable") {
    return upstreamCacheControl;
  }
  const mediaRead = upstreamPath.startsWith(APPROVED_MEDIA_PREFIX) && ["GET", "HEAD"].includes(method);
  if (!mediaRead || !ok || hasSetCookie) return PRIVATE_NO_STORE;

  const upstreamPolicy = upstreamCacheControl?.trim();
  if (upstreamPolicy) {
    if (/\b(no-store|private)\b/i.test(upstreamPolicy)) return PRIVATE_NO_STORE;
    if (/(^|,)\s*public\b/i.test(upstreamPolicy)) return upstreamPolicy;
    return PRIVATE_NO_STORE;
  }

  return "public, max-age=86400";
}
