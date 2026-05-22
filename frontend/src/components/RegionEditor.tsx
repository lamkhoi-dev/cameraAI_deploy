import { useRef, type MouseEvent } from "react";
import { Button } from "@/components/ui/button";

type Point = [number, number];

interface RegionEditorProps {
  value: Point[];
  onChange: (next: Point[]) => void;
}

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value));
}

export function RegionEditor({ value, onChange }: RegionEditorProps) {
  const stageRef = useRef<HTMLDivElement>(null);

  const addPoint = (event: MouseEvent<HTMLDivElement>) => {
    const rect = stageRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = clamp01((event.clientX - rect.left) / rect.width);
    const y = clamp01((event.clientY - rect.top) / rect.height);
    onChange([...value, [Number(x.toFixed(4)), Number(y.toFixed(4))]]);
  };

  const makeDefaultRegion = () => {
    onChange([
      [0.12, 0.18],
      [0.88, 0.18],
      [0.88, 0.82],
      [0.12, 0.82],
    ]);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-zinc-200 font-medium">Vùng AI xử lý</p>
          <p className="text-xs text-zinc-500">Click để thêm điểm. Tối thiểu 3 điểm để tạo đa giác.</p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="outline" className="border-zinc-700 text-zinc-300" onClick={makeDefaultRegion}>
            Khung mặc định
          </Button>
          <Button type="button" variant="outline" className="border-zinc-700 text-zinc-300" onClick={() => onChange(value.slice(0, -1))} disabled={value.length === 0}>
            Hoàn tác
          </Button>
          <Button type="button" variant="outline" className="border-zinc-700 text-zinc-300" onClick={() => onChange([])} disabled={value.length === 0}>
            Xóa
          </Button>
        </div>
      </div>

      <div
        ref={stageRef}
        onClick={addPoint}
        className="relative h-64 rounded-xl border border-zinc-700 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.08)_1px,transparent_0)] [background-size:24px_24px] overflow-hidden cursor-crosshair"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-amber-500/5" />

        {value.length >= 2 && (
          <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polyline
              points={value.map(([x, y]) => `${x * 100},${y * 100}`).join(" ")}
              stroke="rgba(34,197,94,0.9)"
              strokeWidth="0.8"
            />
            {value.length >= 3 && (
              <polygon
                points={value.map(([x, y]) => `${x * 100},${y * 100}`).join(" ")}
                fill="rgba(34,197,94,0.18)"
                stroke="rgba(34,197,94,0.9)"
                strokeWidth="0.8"
              />
            )}
            {value.map(([x, y], index) => (
              <g key={index}>
                <circle cx={x * 100} cy={y * 100} r="1.4" fill="white" stroke="rgba(34,197,94,0.95)" strokeWidth="0.8" />
                <text x={x * 100 + 1.4} y={y * 100 - 1.4} fill="rgba(255,255,255,0.85)" fontSize="3">
                  {index + 1}
                </text>
              </g>
            ))}
          </svg>
        )}

        {value.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-zinc-500 text-sm">
            Chưa có điểm nào. Click vào khung để bắt đầu vẽ.
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="text-[11px] text-zinc-500 font-mono break-all">
          {JSON.stringify(value)}
        </div>
      )}
    </div>
  );
}
