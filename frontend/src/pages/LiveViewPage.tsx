import { useState, useEffect, useCallback, useRef } from "react";
import { CameraTile } from "@/components/CameraTile";
import { LayoutGrid, Rows3, Grid3X3, X } from "lucide-react";
import api from "@/api/client";
import { useWebSocket } from "@/hooks/useWebSocket";

interface BackendCamera {
  id: number;
  camera_id: string;
  name: string;
  location: string;
  stream_url: string;
  is_active: boolean;
  connection_status: string;
  ai_detect_person: boolean;
  ai_detect_vehicle: boolean;
  ai_detect_fire: boolean;
  display_interval_seconds?: number;
  resolution: string | null;
  fps: number;
}

type Layout = "2x2" | "3x3" | "4x4";

const getStatus = (cam: BackendCamera): "online" | "offline" =>
  cam.is_active ? "online" : "offline";

const getAiTags = (cam: BackendCamera): string[] =>
  cam.ai_detect_person || cam.ai_detect_vehicle ? ["AI"] : [];

export default function LiveViewPage() {
  const [cameras, setCameras] = useState<BackendCamera[]>([]);
  const [layout, setLayout] = useState<Layout>("3x3");
  const [expandedCam, setExpandedCam] = useState<BackendCamera | null>(null);
  const [cameraEvents, setCameraEvents] = useState<Record<string, { persons: number; vehicles: number }>>({});
  const eventTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const getEventWindowMs = useCallback(
    (cameraId: string) => {
      const camera = cameras.find((item) => item.camera_id === cameraId);
      const seconds = camera?.display_interval_seconds ?? 5;
      return Math.max(1000, seconds * 1000);
    },
    [cameras],
  );

  useWebSocket({
    url: `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/api/ws`,
    onMessage: (data) => {
      const msg = data as { type?: string; payload?: { camera_id?: string; count?: number } };
      if (msg.type === "new_person_detected" && msg.payload?.camera_id) {
        const camId = msg.payload.camera_id;
        const windowMs = getEventWindowMs(camId);
        setCameraEvents((prev) => ({
          ...prev,
          [camId]: { persons: (prev[camId]?.persons || 0) + (msg.payload!.count || 1), vehicles: prev[camId]?.vehicles || 0 },
        }));
        clearTimeout(eventTimers.current[camId]);
        eventTimers.current[camId] = setTimeout(() => {
          setCameraEvents((prev) => { const next = { ...prev }; delete next[camId]; return next; });
        }, windowMs);
      }
      if (msg.type === "new_vehicle_detected" && msg.payload?.camera_id) {
        const camId = msg.payload.camera_id;
        const windowMs = getEventWindowMs(camId);
        setCameraEvents((prev) => ({
          ...prev,
          [camId]: { persons: prev[camId]?.persons || 0, vehicles: (prev[camId]?.vehicles || 0) + (msg.payload!.count || 1) },
        }));
        clearTimeout(eventTimers.current[camId]);
        eventTimers.current[camId] = setTimeout(() => {
          setCameraEvents((prev) => { const next = { ...prev }; delete next[camId]; return next; });
        }, windowMs);
      }
    },
  });

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      const list = res.data.cameras || res.data.data || res.data;
      setCameras(Array.isArray(list) ? list : []);
    } catch (err) {
      console.warn("Failed to fetch cameras:", err);
      setCameras([]);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const layoutConfig: Record<Layout, { cols: string; max: number }> = {
    "2x2": { cols: "grid-cols-2", max: 4 },
    "3x3": { cols: "grid-cols-3", max: 9 },
    "4x4": { cols: "grid-cols-4", max: 16 },
  };

  const { cols, max } = layoutConfig[layout];
  const displayCameras = cameras.slice(0, max);

  if (expandedCam) {
    const status = getStatus(expandedCam);
    return (
      <div className="flex gap-6 h-[calc(100vh-7rem)]">
        {/* Main event image (processed / fallback) */}
        <div className="flex-1 bg-black rounded-lg overflow-hidden relative">
          <div className="w-full h-full">
            <CameraTile
              cameraId={expandedCam.camera_id}
              name={expandedCam.name}
              status={status}
              displayIntervalSeconds={expandedCam.display_interval_seconds}
              resolution={expandedCam.resolution || "1080P / 30FPS"}
              events={cameraEvents[expandedCam.camera_id]}
            />
          </div>
          {/* Overlay info */}
          <div className="absolute inset-x-0 top-0 h-14 bg-gradient-to-b from-black/70 to-transparent z-10 pointer-events-none" />
          <div className="absolute top-3 left-4 z-20 flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${status === "online" ? "bg-emerald-500 animate-pulse" : "bg-zinc-600"}`} />
            <span className="text-sm font-semibold text-white drop-shadow-md">{expandedCam.name}</span>
            {status === "online" && (
                <span className="bg-amber-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-sm ml-2">AI</span>
              )}
          </div>
          <button
            onClick={() => setExpandedCam(null)}
            className="absolute top-3 right-4 z-20 text-zinc-400 hover:text-white transition-colors bg-black/40 rounded-full p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Right: Camera List */}
        <div className="w-[280px] flex flex-col gap-2 overflow-y-auto">
          <h3 className="text-sm font-semibold text-zinc-300 mb-2">Danh sách camera</h3>
          {cameras.map((cam) => {
            const camStatus = getStatus(cam);
            return (
              <button
                key={cam.camera_id}
                onClick={() => setExpandedCam(cam)}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  cam.camera_id === expandedCam.camera_id
                    ? "bg-zinc-800 border-blue-500/50"
                    : "bg-zinc-900 border-zinc-800 hover:bg-zinc-800"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${camStatus === "online" ? "bg-emerald-500" : "bg-zinc-600"}`} />
                  <span className="text-sm text-zinc-200">{cam.name}</span>
                </div>
                <span className="text-[11px] text-zinc-500 mt-1 block">{cam.location}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-7rem)]">
      {/* Layout Switcher */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">
          Dashboard sự kiện ({cameras.length})
        </h2>
        <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
          {(["2x2", "3x3", "4x4"] as Layout[]).map((l) => {
            const icons = { "2x2": LayoutGrid, "3x3": Grid3X3, "4x4": Rows3 };
            const Icon = icons[l];
            return (
              <button
                key={l}
                onClick={() => setLayout(l)}
                className={`px-3 py-1.5 text-sm flex items-center gap-1.5 ${
                  layout === l ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <Icon className="h-4 w-4" />
                {l}
              </button>
            );
          })}
        </div>
      </div>

      {/* Camera Grid */}
      <div className={`grid ${cols} gap-3 flex-1 overflow-y-auto`}>
        {displayCameras.map((cam) => {
          const camStatus = getStatus(cam);
          return (
            <div
              key={cam.camera_id}
              onClick={() => camStatus === "online" && setExpandedCam(cam)}
              className="cursor-pointer"
            >
              <CameraTile
                name={cam.name}
                status={camStatus}
                resolution={cam.resolution || "1080P / 30FPS"}
                aiTags={getAiTags(cam)}
                events={cameraEvents[cam.camera_id]}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
