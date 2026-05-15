import { useState, useRef, useCallback, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { cropUrl } from "@/lib/colors";
import { formatVN } from "@/lib/date";
import { Camera, Clock, Target, User, Car, ZoomIn, Maximize2 } from "lucide-react";

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

/** Annotation viewer: full-frame with bbox overlay + hover magnifier */
function AnnotationViewer({
  fullSrc,
  cropSrc,
  bbox,
  isPerson,
  confidence,
}: {
  fullSrc: string;
  cropSrc: string | null;
  bbox?: number[];
  isPerson: boolean;
  confidence: number;
}) {
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgNat, setImgNat] = useState({ w: 0, h: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [magnifier, setMagnifier] = useState<{ x: number; y: number } | null>(null);
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const MAGNIFIER_SIZE = 220;
  const MAGNIFIER_ZOOM = 3.5;

  const onImgLoad = useCallback(() => {
    if (!imgRef.current) return;
    setImgNat({ w: imgRef.current.naturalWidth, h: imgRef.current.naturalHeight });
  }, []);

  // Compute bbox position as CSS % relative to image natural size
  const getBboxStyle = (): React.CSSProperties | null => {
    if (!bbox || bbox.length < 4 || !imgNat.w || !imgNat.h) return null;
    const [x1, y1, x2, y2] = bbox;
    return {
      left: `${(x1 / imgNat.w) * 100}%`,
      top: `${(y1 / imgNat.h) * 100}%`,
      width: `${((x2 - x1) / imgNat.w) * 100}%`,
      height: `${((y2 - y1) / imgNat.h) * 100}%`,
    };
  };

  const bboxStyle = getBboxStyle();
  const bboxColor = isPerson ? "rgba(59,130,246,0.85)" : "rgba(16,185,129,0.85)";
  const bboxGlow = isPerson ? "rgba(59,130,246,0.15)" : "rgba(16,185,129,0.15)";
  const conf = Math.round(confidence * 100);

  // Delayed hover to prevent accidental trigger
  const onBboxEnter = useCallback(() => {
    hoverTimerRef.current = setTimeout(() => setIsHovering(true), 150);
  }, []);

  const onBboxLeave = useCallback(() => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    setIsHovering(false);
    setMagnifier(null);
  }, []);

  const onBboxMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = imgRef.current?.getBoundingClientRect();
    if (!rect) return;
    setMagnifier({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  const getMagnifierStyle = (): React.CSSProperties => {
    if (!magnifier || !imgRef.current) return {};
    const el = imgRef.current;
    const bgW = el.offsetWidth * MAGNIFIER_ZOOM;
    const bgH = el.offsetHeight * MAGNIFIER_ZOOM;
    const bx = magnifier.x * MAGNIFIER_ZOOM - MAGNIFIER_SIZE / 2;
    const by = magnifier.y * MAGNIFIER_ZOOM - MAGNIFIER_SIZE / 2;
    return {
      backgroundImage: `url(${fullSrc})`,
      backgroundSize: `${bgW}px ${bgH}px`,
      backgroundPosition: `-${bx}px -${by}px`,
      left: magnifier.x - MAGNIFIER_SIZE / 2,
      top: magnifier.y - MAGNIFIER_SIZE / 2,
      width: MAGNIFIER_SIZE,
      height: MAGNIFIER_SIZE,
    };
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => { if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current); };
  }, []);

  return (
    <div className="relative bg-zinc-950 flex items-center justify-center select-none overflow-hidden">
      <div className="relative inline-block w-full">
        <img
          ref={imgRef}
          src={fullSrc}
          alt="Full frame"
          className="w-full max-h-[70vh] object-contain"
          onLoad={onImgLoad}
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          draggable={false}
        />

        {/* Bbox overlay */}
        {bboxStyle && (
          <div
            className="absolute transition-all duration-200 ease-out"
            style={{
              ...bboxStyle,
              border: `2.5px solid ${bboxColor}`,
              backgroundColor: isHovering ? bboxGlow : "transparent",
              boxShadow: isHovering
                ? `0 0 24px ${bboxColor}, inset 0 0 30px ${bboxGlow}`
                : `0 0 0 1px ${bboxColor}`,
              cursor: "crosshair",
              zIndex: 10,
            }}
            onMouseEnter={onBboxEnter}
            onMouseLeave={onBboxLeave}
            onMouseMove={onBboxMouseMove}
          >
            {/* Label */}
            <div
              className="absolute -top-6 left-0 px-2 py-0.5 text-[11px] font-bold text-white whitespace-nowrap rounded-t-sm"
              style={{ backgroundColor: bboxColor }}
            >
              {isPerson ? "👤 PERSON" : "🚗 VEHICLE"} · {conf}%
            </div>

            {/* Corner markers */}
            {[
              "-top-[2px] -left-[2px] border-t-[3px] border-l-[3px]",
              "-top-[2px] -right-[2px] border-t-[3px] border-r-[3px]",
              "-bottom-[2px] -left-[2px] border-b-[3px] border-l-[3px]",
              "-bottom-[2px] -right-[2px] border-b-[3px] border-r-[3px]",
            ].map((pos, i) => (
              <div key={i} className={`absolute w-4 h-4 ${pos}`} style={{ borderColor: bboxColor }} />
            ))}
          </div>
        )}

        {/* Magnifier lens — only appears after hover delay */}
        {isHovering && magnifier && (
          <div
            className="absolute rounded-full border-[3px] border-white/80 shadow-2xl pointer-events-none z-50 overflow-hidden"
            style={{
              ...getMagnifierStyle(),
              boxShadow: "0 0 0 2px rgba(0,0,0,0.3), 0 8px 32px rgba(0,0,0,0.5)",
            }}
          />
        )}

        {/* Hint */}
        {bboxStyle && !isHovering && (
          <div className="absolute bottom-3 right-3 opacity-80 bg-black/80 backdrop-blur-sm rounded-lg px-3 py-1.5 flex items-center gap-1.5 pointer-events-none text-[11px] text-zinc-200 z-20">
            <ZoomIn className="h-3.5 w-3.5" /> Rê chuột vào khung để phóng to
          </div>
        )}
      </div>

      {/* Crop mini-thumbnail */}
      {cropSrc && (
        <div className="absolute top-3 left-3 z-20">
          <div className="w-14 h-18 rounded-lg border border-zinc-600/40 overflow-hidden bg-zinc-900/90 shadow-xl backdrop-blur-sm">
            <img src={cropSrc} alt="Crop" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
          </div>
          <div className="text-[8px] text-zinc-500 mt-0.5 text-center">Crop</div>
        </div>
      )}
    </div>
  );
}

/** Simple crop viewer with click-to-zoom */
function CropViewer({ src }: { src: string }) {
  const [zoomed, setZoomed] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setZoomed(false); };
    if (zoomed) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [zoomed]);

  return (
    <>
      {zoomed && (
        <div className="fixed inset-0 z-[100] bg-black/95 backdrop-blur-sm flex items-center justify-center cursor-zoom-out" onClick={() => setZoomed(false)}>
          <img src={src} alt="Zoom" className="max-w-[95vw] max-h-[95vh] object-contain" />
        </div>
      )}
      <div className="relative group flex items-center justify-center bg-zinc-950 min-h-[200px]">
        <img
          src={src}
          alt="Crop"
          className="max-w-full max-h-[50vh] object-contain cursor-zoom-in"
          onClick={() => setZoomed(true)}
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
        <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded-md px-2 py-1 flex items-center gap-1 pointer-events-none text-[10px] text-zinc-400">
          <ZoomIn className="h-3 w-3" /> Click để phóng to
        </div>
      </div>
    </>
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
  const hasFullFrame = !!fullSrc && !!detection.bbox?.length;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className={`bg-zinc-900 border-zinc-800 text-zinc-100 p-0 overflow-hidden ${
          hasFullFrame ? "sm:max-w-5xl" : "sm:max-w-lg"
        }`}
      >
        <DialogHeader className="p-4 pb-0">
          <DialogTitle className="flex items-center gap-2">
            {isPerson ? <User className="h-5 w-5 text-blue-400" /> : <Car className="h-5 w-5 text-emerald-400" />}
            Chi tiết {isPerson ? "Người" : "Phương tiện"}
            {hasFullFrame && (
              <Badge className="ml-auto text-[10px] bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                <Maximize2 className="h-3 w-3 mr-1" /> Full Frame + BBox
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        {/* Image area */}
        <div className="border-y border-zinc-800">
          {hasFullFrame ? (
            <AnnotationViewer
              fullSrc={fullSrc!}
              cropSrc={cropSrc}
              bbox={detection.bbox}
              isPerson={isPerson}
              confidence={detection.confidence}
            />
          ) : cropSrc ? (
            <CropViewer src={cropSrc} />
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
  );
}

export type { DetectionDetail, ColorInfo };
