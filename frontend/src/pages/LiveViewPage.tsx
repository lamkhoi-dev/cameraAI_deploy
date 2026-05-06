import { useState, useEffect, useCallback } from "react";
import { CameraTile } from "@/components/CameraTile";
import { LayoutGrid, Rows3, Grid3X3, X } from "lucide-react";
import api from "@/api/client";

const GO2RTC_BASE = import.meta.env.VITE_GO2RTC_BASE || "/go2rtc";
// Absolute base for iframes (must be full URL)
const go2rtcAbsolute = () =>
  typeof window !== "undefined" && GO2RTC_BASE.startsWith("/")
    ? `${window.location.origin}${GO2RTC_BASE}`
    : GO2RTC_BASE;

interface BackendCamera {
  id: number;
  camera_id: string;
  name: string;
  location: string;
  stream_url: string;
  is_active: boolean;
  last_connection_status: string;
  enable_detection: boolean;
  resolution: string | null;
  fps: number;
}

type Layout = "2x2" | "3x3" | "4x4";

const getStatus = (cam: BackendCamera): "online" | "offline" =>
  cam.is_active ? "online" : "offline";

const getAiTags = (cam: BackendCamera): string[] =>
  cam.enable_detection ? ["AI Active"] : [];

export default function LiveViewPage() {
  const [cameras, setCameras] = useState<BackendCamera[]>([]);
  const [layout, setLayout] = useState<Layout>("3x3");
  const [expandedCam, setExpandedCam] = useState<BackendCamera | null>(null);

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      const list = res.data.data || res.data;
      setCameras(Array.isArray(list) ? list : []);
    } catch {
      setCameras([
        { id: 1, camera_id: "cam_01", name: "Sảnh A / Tầng 1", location: "Sảnh A", stream_url: "rtsp://localhost:8554/cam_01", is_active: true, last_connection_status: "connected", enable_detection: true, resolution: "1920x1080", fps: 30 },
        { id: 2, camera_id: "cam_02", name: "Bãi xe B1", location: "Bãi xe", stream_url: "rtsp://localhost:8554/cam_02", is_active: true, last_connection_status: "connected", enable_detection: true, resolution: "1920x1080", fps: 30 },
        { id: 3, camera_id: "cam_03", name: "Hành lang C", location: "Hành lang", stream_url: "rtsp://localhost:8554/cam_03", is_active: true, last_connection_status: "disconnected", enable_detection: false, resolution: "1920x1080", fps: 30 },
        { id: 4, camera_id: "cam_04", name: "Kho Hàng / Tầng 2", location: "Kho hàng", stream_url: "rtsp://localhost:8554/cam_04", is_active: false, last_connection_status: "disconnected", enable_detection: false, resolution: null, fps: 30 },
      ]);
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
        {/* Main Video */}
        <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${status === "online" ? "bg-emerald-500" : "bg-zinc-600"}`} />
              <span className="text-sm font-semibold text-white">{expandedCam.name}</span>
              {status === "online" && (
                <span className="bg-red-500/20 border border-red-500/50 text-red-500 text-[11px] font-medium px-1.5 py-0.5 rounded-sm animate-pulse ml-2">
                  LIVE
                </span>
              )}
            </div>
            <button
              onClick={() => setExpandedCam(null)}
              className="text-zinc-400 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex-1 bg-black relative">
            <iframe
              src={`${go2rtcAbsolute()}/stream.html?src=${expandedCam.camera_id}&mode=webrtc`}
              className="w-full h-full border-0"
              allow="autoplay; fullscreen"
              title={expandedCam.name}
            />
          </div>
        </div>

        {/* Right: Camera Thumbnails */}
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
                  <span
                    className={`w-2 h-2 rounded-full ${camStatus === "online" ? "bg-emerald-500" : "bg-zinc-600"}`}
                  />
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
          Camera trực tiếp ({cameras.length})
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
                  layout === l
                    ? "bg-zinc-800 text-zinc-100"
                    : "text-zinc-500 hover:text-zinc-300"
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
      <div className={`grid ${cols} gap-4 flex-1 overflow-y-auto`}>
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
                streamUrl={
                  camStatus === "online"
                    ? `${go2rtcAbsolute()}/stream.html?src=${cam.camera_id}&mode=webrtc`
                    : undefined
                }
                aiTags={getAiTags(cam)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
