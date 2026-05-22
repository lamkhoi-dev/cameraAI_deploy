
import { VideoOff, Users, Car } from "lucide-react";
import { useEffect, useState, useRef, useCallback } from "react";
import api from "@/api/client";

interface CameraTileProps {
  cameraId?: string;
  name: string;
  status: "online" | "offline";
  resolution?: string;
  protocol?: string;
  aiTags?: string[];
  events?: { persons: number; vehicles: number };
  displayIntervalSeconds?: number;
}

interface DisplayImageResponse {
  type?: "ai" | "fallback";
  image_url?: string;
  image_base64?: string;
  confidence?: number;
  timestamp?: string;
  bbox?: number[];
}

export function CameraTile({
  cameraId,
  name,
  status,
  resolution = "1080P / 30FPS",
  protocol = "RTC",
  aiTags: _aiTags = [],
  events,
  displayIntervalSeconds = 5,
}: CameraTileProps) {
  const isOnline = status === "online";
  const [showEvent, setShowEvent] = useState(false);
  const [eventData, setEventData] = useState({ persons: 0, vehicles: 0 });
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [imageMeta, setImageMeta] = useState<DisplayImageResponse | null>(null);
  const [imageBox, setImageBox] = useState<{ left: number; top: number; width: number; height: number } | null>(null);
  const pollingRef = useRef<number | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const frameRef = useRef<HTMLDivElement>(null);

  const updateImageBox = useCallback(() => {
    if (!imgRef.current || !frameRef.current || !imageMeta?.bbox || imageMeta.bbox.length < 4) {
      setImageBox(null);
      return;
    }

    const [x1, y1, x2, y2] = imageMeta.bbox;
    const naturalWidth = imgRef.current.naturalWidth || 0;
    const naturalHeight = imgRef.current.naturalHeight || 0;
    const container = frameRef.current.getBoundingClientRect();
    if (!naturalWidth || !naturalHeight || !container.width || !container.height) {
      setImageBox(null);
      return;
    }

    const imageAspect = naturalWidth / naturalHeight;
    const containerAspect = container.width / container.height;

    let drawnWidth = container.width;
    let drawnHeight = container.height;
    let offsetX = 0;
    let offsetY = 0;

    if (imageAspect > containerAspect) {
      drawnHeight = container.width / imageAspect;
      offsetY = (container.height - drawnHeight) / 2;
    } else {
      drawnWidth = container.height * imageAspect;
      offsetX = (container.width - drawnWidth) / 2;
    }

    setImageBox({
      left: offsetX + (x1 / naturalWidth) * drawnWidth,
      top: offsetY + (y1 / naturalHeight) * drawnHeight,
      width: ((x2 - x1) / naturalWidth) * drawnWidth,
      height: ((y2 - y1) / naturalHeight) * drawnHeight,
    });
  }, [imageMeta]);

  useEffect(() => {
    if (!events || (events.persons === 0 && events.vehicles === 0)) return;
    setEventData(events);
    setShowEvent(true);
    const timer = setTimeout(() => setShowEvent(false), 4000);
    return () => clearTimeout(timer);
  }, [events]);

  useEffect(() => {
    async function fetchImage() {
      if (!cameraId) return;
      try {
        const res = await api.get(`/cameras/${cameraId}/display_image`);
        if (res.status === 200 && res.data) {
          const d = res.data as DisplayImageResponse;
          setImageMeta(d);
          if (d.image_url) setImageSrc(d.image_url);
          else if (d.image_base64) setImageSrc(`data:image/jpeg;base64,${d.image_base64}`);
        }
      } catch (err: any) {
        if (err?.response?.status === 204) return; // nothing to show yet
        // ignore other errors silently
      }
    }

    // initial fetch
    fetchImage();

    // set interval
    const intervalMs = Math.max(1000, (displayIntervalSeconds || 5) * 1000);
    const id = window.setInterval(fetchImage, intervalMs);
    pollingRef.current = id;

    return () => {
      if (pollingRef.current) window.clearInterval(pollingRef.current);
    };
  }, [cameraId, displayIntervalSeconds]);

  useEffect(() => {
    updateImageBox();
    window.addEventListener("resize", updateImageBox);
    return () => window.removeEventListener("resize", updateImageBox);
  }, [updateImageBox, imageSrc]);

  return (
    <div className="relative bg-black rounded-lg overflow-hidden aspect-video group">
      {isOnline ? (
        <>
          {/* Display processed image (polled) or fallback image */}
          <div ref={frameRef} className="absolute inset-0">
          {imageSrc ? (
            <img
              ref={imgRef}
              src={imageSrc}
              alt={name}
              className="absolute inset-0 w-full h-full object-contain bg-black"
              onLoad={updateImageBox}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
              <span className="text-zinc-500">No image yet</span>
            </div>
          )}
          {imageBox && imageMeta?.type === "ai" && (
            <div
              className="absolute pointer-events-none rounded-sm border-2"
              style={{
                left: imageBox.left,
                top: imageBox.top,
                width: imageBox.width,
                height: imageBox.height,
                borderColor: "rgba(56, 189, 248, 0.95)",
                boxShadow: "0 0 16px rgba(56, 189, 248, 0.35)",
              }}
            >
              <span className="absolute -top-6 left-0 bg-sky-500/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-sm">
                AI {Math.round((imageMeta.confidence || 0) * 100)}%
              </span>
            </div>
          )}
          </div>

          {/* Scanline overlay */}
          <div
            className="absolute inset-0 z-10 pointer-events-none"
            style={{
              background:
                "linear-gradient(to bottom, transparent, transparent 50%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.1))",
              backgroundSize: "100% 4px",
            }}
          />

          {/* Gradient overlays for text readability */}
          <div className="absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-black/70 to-transparent z-20 pointer-events-none" />
          <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-black/70 to-transparent z-20 pointer-events-none" />

          {/* Top-left: Status + Name */}
          <div className="absolute top-2 left-2.5 z-30 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-semibold text-white drop-shadow-md tracking-wide">{name}</span>
          </div>

          {/* Top-right: STATUS badge */}
          <div className="absolute top-2 right-2.5 z-30">
            <span className="bg-amber-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-sm tracking-wider">
              AI
            </span>
          </div>

          {/* Bottom-left: Resolution */}
          <div className="absolute bottom-2 left-2.5 z-30">
            <span className="text-[10px] font-medium text-zinc-300/90 drop-shadow-md">{resolution}</span>
          </div>

          {/* Bottom-right: Protocol */}
          <div className="absolute bottom-2 right-2.5 z-30">
            <span className="text-[10px] font-medium text-zinc-400/80 drop-shadow-md">{protocol}</span>
          </div>

          {/* Top-center: EVENT REALTIME — always on */}
          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-30">
            <span className="text-[11px] font-extrabold tracking-widest text-red-400/80 uppercase drop-shadow-md select-none">
              EVENT REALTIME
            </span>
          </div>

          {/* Event counts — bottom center, only when active */}
          {showEvent && (eventData.persons > 0 || eventData.vehicles > 0) && (
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30">
              <div className="flex items-center gap-2 bg-black/70 backdrop-blur-sm border border-zinc-700/50 rounded-full px-3 py-1 animate-in fade-in duration-300">
                {eventData.persons > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-blue-400 font-medium">
                    <Users className="h-3 w-3" /> {eventData.persons}
                  </span>
                )}
                {eventData.vehicles > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                    <Car className="h-3 w-3" /> {eventData.vehicles}
                  </span>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        /* Offline state */
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-zinc-950">
          <VideoOff className="h-7 w-7 text-zinc-700" />
          <span className="text-[11px] font-medium text-zinc-600 tracking-wider">
            {name}
          </span>
          <span className="text-[10px] text-zinc-700">OFFLINE</span>
        </div>
      )}
    </div>
  );
}
