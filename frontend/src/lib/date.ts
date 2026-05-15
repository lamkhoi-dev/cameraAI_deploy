/**
 * Format ISO timestamp to Vietnam timezone (UTC+7)
 */
export function formatVN(iso: string | null | undefined, opts?: { dateOnly?: boolean }): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (opts?.dateOnly) {
      return d.toLocaleDateString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", day: "2-digit", month: "2-digit", year: "numeric" });
    }
    return d.toLocaleString("vi-VN", {
      timeZone: "Asia/Ho_Chi_Minh",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

/**
 * Format time only (HH:mm:ss) in Vietnam timezone
 */
export function formatVNTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleTimeString("vi-VN", {
      timeZone: "Asia/Ho_Chi_Minh",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}
