/** Color definitions matching AI engine ColorAnalyzer output */
export const COLOR_MAP: Record<string, string> = {
  "Đỏ": "#EF4444",
  "Cam": "#F97316",
  "Vàng": "#EAB308",
  "Vàng lục": "#84CC16",
  "Lục": "#22C55E",
  "Xanh lục": "#06B6D4",
  "Xanh lam": "#0EA5E9",
  "Xanh dương": "#3B82F6",
  "Tím": "#8B5CF6",
  "Hồng": "#EC4899",
  "Đỏ tím": "#DB2777",
  "Đen": "#1F2937",
  "Trắng": "#F9FAFB",
  "Xám": "#6B7280",
  "Nâu": "#92400E",
};

export const ALL_COLORS = Object.keys(COLOR_MAP);

export function cropUrl(imagePath: string | null | undefined): string | null {
  if (!imagePath) return null;
  // Convert /app/cropped_data/persons/xxx.jpg → /api/crops/persons/xxx.jpg
  return imagePath.replace(/^\/app\/cropped_data/, "/api/crops");
}
