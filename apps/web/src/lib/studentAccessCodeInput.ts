/** Convert Arabic/Persian keypad digits to ASCII for six-digit student access codes.
 * This changes input representation only; it does not create or validate a credential.
 */
export function normalizeStudentAccessCodeInput(value: string): string {
  return value
    .replace(/[٠-٩]/g, digit => String(digit.charCodeAt(0) - 0x0660))
    .replace(/[۰-۹]/g, digit => String(digit.charCodeAt(0) - 0x06f0))
    .replace(/[^0-9]/g, "")
    .slice(0, 6);
}
