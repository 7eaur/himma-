/**
 * Display-only Arabic shaping for separated word-building tiles.
 *
 * The server grades immutable option IDs. The position shown here is ONLY the
 * child's selected order, or a worked model the server has already explicitly
 * released during support practice. Never infer the private correct order from
 * an unselected options list (it would give away independent-check answers).
 *
 * Each tile lives in its own DOM box, so its Arabic letter cannot join the
 * neighbour through the browser's font shaping. Tatweel makes the same letter
 * take its initial/medial/final form inside its own box.
 */
const TATWEEL = "\u0640";
const ONE_ARABIC_LETTER = /^([\u0621-\u063A\u0641-\u064A\u066E\u066F\u0671-\u06D3])([\u064B-\u065F\u0670]*)$/u;

// These letters never connect to the *following* letter in written Arabic.
// In particular ر breaks the join before ة in "كرة": كـ / ـر / ة.
const NO_FORWARD_JOIN = new Set([
  "ء", "آ", "أ", "ؤ", "إ", "ا", "ٱ", "ة", "د", "ذ", "ر", "ز",
  "ژ", "و", "ى", "ڈ", "ډ", "ڋ", "ڌ", "ڍ", "ڎ", "ڏ", "ڐ",
  "ڑ", "ڕ", "ږ", "ۅ", "ۆ", "ۇ", "ۈ", "ۉ", "ۋ", "ې",
]);

// Hamza alone has no incoming join; alif/raa/taa marbuta can join from
// their right-hand (preceding) neighbour, but cannot join to the next one.
const NO_BACKWARD_JOIN = new Set(["ء"]);

function singleArabicLetter(text: string): { base: string; marks: string } | null {
  const match = ONE_ARABIC_LETTER.exec(text.normalize("NFC"));
  return match ? { base: match[1], marks: match[2] } : null;
}

/**
 * "كرة" -> ["كـ", "ـر", "ة"]
 * "شمس" -> ["شـ", "ـمـ", "ـس"]
 * "باب" -> ["بـ", "ـا", "ب"]
 * The visual elongation never becomes a submitted answer or content change.
 */
export function shapeArabicWordTiles(texts: readonly string[]): string[] {
  const letters = texts.map(singleArabicLetter);
  return texts.map((text, index) => {
    const current = letters[index];
    if (!current) return text; // Preserve multi-letter options, spaces and punctuation.
    const previous = letters[index - 1];
    const next = letters[index + 1];
    const joinsPrevious = Boolean(previous
      && !NO_FORWARD_JOIN.has(previous.base)
      && !NO_BACKWARD_JOIN.has(current.base));
    const joinsNext = Boolean(next
      && !NO_FORWARD_JOIN.has(current.base)
      && !NO_BACKWARD_JOIN.has(next.base));
    return (joinsPrevious ? TATWEEL : "")
      + current.base + current.marks
      + (joinsNext ? TATWEEL : "");
  });
}
