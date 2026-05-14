import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { cropUrl } from "@/lib/colors";
import { Camera, Clock, Target, User, Car } from "lucide-react";

interface ColorInfo {
  rank: number;
  name: string;
  rgb: number[];
}

interface DetectionDetail {
  id: string;
  type: "person" | "vehicle";
  camera: string;
  timestamp: string;
  confidence: number;
  track_id?: number;
  image_path?: string;
  shirt_colors?: ColorInfo[];
  pants_colors?: ColorInfo[];
  hair_colors?: ColorInfo[];
  vehicle_type?: string;
  vehicle_colors?: ColorInfo[];
  license_plate?: string;
}

function ColorDots({ label, colors }: { label: string; colors?: ColorInfo[] }) {
  if (!colors?.length) return null;
  return (
    <div className="flex items-center gap-2">
      <span className="text-zinc-500 text-xs w-16">{label}</span>
      <div className="flex gap-1.5 flex-wrap">
        {colors.map((c, i) => (
          <div key={i} className="flex items-center gap-1">
            <span
              className="w-4 h-4 rounded-full border border-zinc-600 inline-block"
              style={{ backgroundColor: `rgb(${c.rgb.join(",")})` }}
            />
            <span className="text-xs text-zinc-400">{c.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DetectionModal({
  detection,
  open,
  onClose,
}: {
  detection: DetectionDetail | null;
  open: boolean;
  onClose: () => void;
}) {
  if (!detection) return null;
  const imgSrc = cropUrl(detection.image_path);
  const isPerson = detection.type === "person";
  const conf = Math.round(detection.confidence * 100);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 max-w-md p-0 overflow-hidden">
        <DialogHeader className="p-4 pb-0">
          <DialogTitle className="flex items-center gap-2">
            {isPerson ? <User className="h-5 w-5 text-blue-400" /> : <Car className="h-5 w-5 text-emerald-400" />}
            Chi tiết {isPerson ? "Người" : "Phương tiện"}
          </DialogTitle>
        </DialogHeader>

        {/* Image — natural aspect ratio, max height constrained */}
        <div className="bg-zinc-950 flex items-center justify-center border-y border-zinc-800 min-h-[120px] max-h-[400px]">
          {imgSrc ? (
            <img
              src={imgSrc}
              alt="Crop"
              className="max-w-full max-h-[400px] object-contain"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          ) : (
            <div className="py-12 text-zinc-600 text-sm">Không có ảnh</div>
          )}
        </div>

        {/* Info grid */}
        <div className="p-4 pt-3 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 text-sm">
              <Camera className="h-4 w-4 text-zinc-500 flex-shrink-0" />
              <span className="text-zinc-300">{detection.camera}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-zinc-500 flex-shrink-0" />
              <span className="text-zinc-300 font-mono text-xs">{detection.timestamp}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Target className="h-4 w-4 text-zinc-500 flex-shrink-0" />
              <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${conf >= 80 ? "bg-emerald-500" : conf >= 60 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${conf}%` }} />
                </div>
                <span className="text-zinc-300 text-xs font-mono">{conf}%</span>
              </div>
            </div>
            {detection.track_id != null && (
              <div className="flex items-center">
                <Badge className="bg-zinc-800 text-zinc-400 text-[10px]">Track #{detection.track_id}</Badge>
              </div>
            )}
          </div>

          <div className="border-t border-zinc-800 pt-3 space-y-2">
            {isPerson ? (
              <>
                <ColorDots label="Áo" colors={detection.shirt_colors} />
                <ColorDots label="Quần" colors={detection.pants_colors} />
                <ColorDots label="Tóc" colors={detection.hair_colors} />
              </>
            ) : (
              <>
                {detection.vehicle_type && (
                  <div className="text-sm text-zinc-300">Loại: <span className="text-zinc-100 font-medium">{detection.vehicle_type}</span></div>
                )}
                {detection.license_plate && (
                  <div className="text-sm text-zinc-300">Biển số: <span className="text-amber-400 font-mono font-medium">{detection.license_plate}</span></div>
                )}
                <ColorDots label="Màu xe" colors={detection.vehicle_colors} />
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export type { DetectionDetail, ColorInfo };
