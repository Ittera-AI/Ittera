/**
 * Thread content helpers.
 *
 * Twitter thread drafts are persisted with `content` as a JSON-encoded array of
 * strings, e.g. `'["First tweet", "Second tweet"]'`. Single posts are stored as
 * a plain string. These helpers convert between the stored representation and an
 * editable plain-text representation used in the draft editor.
 *
 * Editable representation: segments joined by a visible separator line so users
 * can see and adjust thread breaks. On save we split back on the same separator.
 */

/** Visible separator shown between thread segments in the editor textarea. */
export const THREAD_SEPARATOR = "\n\n---\n\n";

/** Regex used to split the editable text back into segments (tolerant of surrounding whitespace). */
const THREAD_SPLIT_RE = /\n\s*-{3,}\s*\n/;

/**
 * Returns the parsed segments if `content` is a JSON array of strings with more
 * than one entry (i.e. a real thread), otherwise `null`.
 */
export function parseThreadSegments(content: string | null | undefined): string[] | null {
  if (!content) return null;
  try {
    const parsed = JSON.parse(content);
    if (Array.isArray(parsed) && parsed.length > 1 && parsed.every((s) => typeof s === "string")) {
      return parsed as string[];
    }
  } catch {
    // Not JSON — a plain single-post draft.
  }
  return null;
}

/** True when the stored content represents a multi-segment thread. */
export function isThreadContent(content: string | null | undefined): boolean {
  return parseThreadSegments(content) !== null;
}

/**
 * Convert stored draft content into editable plain text.
 * - Thread → segments joined by the visible separator.
 * - Single post → returned as-is.
 */
export function toEditableText(content: string | null | undefined): string {
  const segments = parseThreadSegments(content);
  if (segments) {
    return segments.join(THREAD_SEPARATOR);
  }
  return content ?? "";
}

/**
 * Convert editable plain text back into the stored representation.
 * - If the text contains the thread separator, serialize as a JSON array.
 * - Otherwise return the plain string unchanged.
 */
export function fromEditableText(text: string): string {
  if (THREAD_SPLIT_RE.test(text)) {
    const segments = text
      .split(THREAD_SPLIT_RE)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    if (segments.length > 1) {
      return JSON.stringify(segments);
    }
    // Collapsed to a single segment after trimming — store as plain text.
    return segments[0] ?? "";
  }
  return text;
}

/** Number of segments in the editable text (1 for a single post). */
export function countSegments(text: string): number {
  if (!text.trim()) return 0;
  if (THREAD_SPLIT_RE.test(text)) {
    return text
      .split(THREAD_SPLIT_RE)
      .map((s) => s.trim())
      .filter((s) => s.length > 0).length;
  }
  return 1;
}
