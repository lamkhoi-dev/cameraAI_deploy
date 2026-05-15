import { useState, useEffect, useRef, useCallback } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { cropUrl } from "@/lib/colors";
import { formatVN } from "@/lib/date";
import { Camera, Clock, Target, User, Car, X, ZoomIn, Image } from "lucide-react";

// Toggle: true = full frame + hover magnifier | false = crop + click lightbox
const USE_FULL_FRAME = import.meta.env.VITE_FULL_FRAME_MODE === "true";

const MAGNIFIER_SIZE = 160;  // px diameter of magnifier lens
const MAGNIFIER_ZOOM = 2.8;  // zoom multiplier

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
  full_frame_path?: string;
  bbox?: number[];
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

/** CSS Magnifier Lens — follows cursor over an image */
function MagnifierImage({ src, alt }: { src: string; alt: string }) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [lens, setLens] = useState<{ x: number; y: number } | null>(null);
  const [naturalSize, setNaturalSize] = useState({ w: 0, h: 0 });

  const onLoad = useCallback(() => {
    if (imgRef.current) {
      setNaturalSize({ w: imgRef.current.naturalWidth, h: imgRef.current.naturalHeight });
    }
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
    setLens({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  const onMouseLeave = useCallback(() => setLens(null), []);

  // Compute background-position for magnifier
  const getMagnifierStyle = (): React.CSSProperties => {
    if (!lens || !imgRef.current) return {};
    const el = imgRef.current;
    const rx = el.offsetWidth / naturalSize.w;
    const ry = el.offsetHeight / naturalSize.h;
    const bx = lens.x * MAGNIFIER_ZOOM - MAGNIFIER_SIZE / 2;
    const by = lens.y * MAGNIFIER_ZOOM - MAGNIFIER_SIZE / 2;
    return {
      backgroundImage: `url(${src})`,
      backgroundSize: `${el.offsetWidth * MAGNIFIER_ZOOM}px ${el.offsetHeight * MAGNIFIER_ZOOM}px`,
      backgroundPosition: `-${bx}px -${by}px`,
      left: lens.x - MAGNIFIER_SIZE / 2,
      top: lens.y - MAGNIFIER_SIZE / 2,
      width: MAGNIFIER_SIZE,
      height: MAGNIFIER_SIZE,
    };
  };

  return (
    <div
      className="relative w-full flex items-center justify-center select-none"
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      style={{ cursor: "none" }}
    >
      <img
        ref={imgRef}
        src={src}
        alt={alt}
        className="max-w-full max-h-[400px] object-contain"
        onLoad={onLoad}
        onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        draggable={false}
      />
      {/* Magnifier lens */}
      {lens && (
        <div
          className="absolute rounded-full border-2 border-white/60 shadow-2xl pointer-events-none z-50 overflow-hidden"
          style={getMagnifierStyle()}
        />
      )}
      {!lens && (
        <div className="absolute bottom-2 right-2 opacity-60 bg-black/60 rounded-md px-2 py-1 flex items-center gap-1 pointer-events-none text-[10px] text-zinc-400">
          <ZoomIn className="h-3 w-3" /> Di chuột để phóng to
        </div>
      )}
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

  const cropSrc = cropUrl(detection.image_path);
  const fullSrc = detection.full_frame_path ? cropUrl(detection.full_frame_path) : null;
  const isPerson = detection.type === "person";
  const conf = Math.round(detection.confidence * 100);

  // Image to display: full frame (if available + mode on) or crop
  const showFull = USE_FULL_FRAME && !!fullSrc;
  const displaySrc = showFull ? fullSrc! : cropSrc;

  // Lightbox state (crop-only mode)
  const [zoomed, setZoomed] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setZoomed(false); };
    if (zoomed) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [zoomed]);

  return (
    <>
      {/* Zoom Lightbox (crop mode only) */}
      {!showFull && zoomed && displaySrc && (
        <div
          className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-sm flex items-center justify-center cursor-zoom-out"
          onClick={() => setZoomed(false)}
        >
          <button onClick={() => setZoomed(false)} className="absolute top-4 right-4 text-zinc-400 hover:text-white z-10">
            <X className="h-6 w-6" />
          </button>
          <img src={displaySrc} alt="Zoom" className="max-w-[95vw] max-h-[95vh] object-contain" />
        </div>
      )}

      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="bg-zinc-900 border-zinc-800 text-zinc-100 max-w-lg p-0 overflow-hidden">
          <DialogHeader className="p-4 pb-0">
            <DialogTitle className="flex items-center gap-2">
              {isPerson ? <User className="h-5 w-5 text-blue-400" /> : <Car className="h-5 w-5 text-emerald-400" />}
              Chi tiết {isPerson ? "Người" : "Phương tiện"}
              {showFull && (
                <Badge className="ml-auto text-[9px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                  <Image className="h-3 w-3 mr-1" /> Full Frame
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>

          {/* Image area */}
          <div className="bg-zinc-950 border-y border-zinc-800 min-h-[120px] relative">
            {displaySrc ? (
              showFull ? (
                /* Full frame mode: hover magnifier */
                <MagnifierImage src={displaySrc} alt="Full frame" />
              ) : (
                /* Crop mode: click to lightbox */
                <div className="relative group flex items-center justify-center">
                  <img
                    src={displaySrc}
                    alt="Crop"
                    className="max-w-full max-h-[400px] object-contain cursor-zoom-in"
                    onClick={() => setZoomed(true)}
                    onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                  />
                  <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded-md px-2 py-1 flex items-center gap-1 pointer-events-none text-[10px] text-zinc-400">
                    <ZoomIn className="h-3 w-3" /> Click để phóng to
                  </div>
                </div>
              )
            ) : (
              <div className="py-12 text-center text-zinc-600 text-sm">Không có ảnh</div>
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
                <span className="text-zinc-300 font-mono text-xs">{formatVN(detection.timestamp)}</span>
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
    </>
  );
}

export type { DetectionDetail, ColorInfo };
