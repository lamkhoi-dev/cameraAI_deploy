import { useState, useEffect, useCallback } from "react";
import { CameraTile } from "@/components/CameraTile";
import { LayoutGrid, Rows3, Grid3X3, X } from "lucide-react";
import api from "@/api/client";

const GO2RTC_BASE = import.meta.env.VITE_GO2RTC_BASE || "http://localhost:1984";

interface Camera {
  id: number;
  name: string;
  location: string;
  status: string;
  stream_id: string;
  ai_features: string[];
}

type Layout = "2x2" | "3x3" | "4x4";

export default function LiveViewPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [layout, setLayout] = useState<Layout>("3x3");
  const [expandedCam, setExpandedCam] = useState<Camera | null>(null);

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      setCameras(res.data);
    } catch {
      setCameras([
        { id: 1, name: "Sảnh A / Tầng 1", location: "Sảnh A", status: "online", stream_id: "cam_01", ai_features: ["Người"] },
        { id: 2, name: "Bãi xe B1", location: "Bãi xe", status: "online", stream_id: "cam_02", ai_features: ["Xe"] },
        { id: 3, name: "Hành lang C", location: "Hành lang", status: "online", stream_id: "cam_03", ai_features: [] },
        { id: 4, name: "Kho Hàng / Tầng 2", location: "Kho hàng", status: "offline", stream_id: "cam_04", ai_features: [] },
        { id: 5, name: "Cổng chính", location: "Cổng", status: "online", stream_id: "cam_05", ai_features: ["Người", "Xe"] },
        { id: 6, name: "Tầng 3 / Văn phòng", location: "Tầng 3", status: "online", stream_id: "cam_06", ai_features: [] },
        { id: 7, name: "Sân sau", location: "Sân sau", status: "online", stream_id: "cam_07", ai_features: [] },
        { id: 8, name: "Thang máy A", location: "Thang máy", status: "online", stream_id: "cam_08", ai_features: ["Người"] },
        { id: 9, name: "Phòng server", location: "Server", status: "online", stream_id: "cam_09", ai_features: [] },
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
    return (
      <div className="flex gap-6 h-[calc(100vh-7rem)]">
        {/* Main Video */}
        <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-sm font-semibold text-white">{expandedCam.name}</span>
              <span className="bg-red-500/20 border border-red-500/50 text-red-500 text-[11px] font-medium px-1.5 py-0.5 rounded-sm animate-pulse ml-2">
                LIVE
              </span>
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
              src={`${GO2RTC_BASE}/stream.html?src=${expandedCam.stream_id}&mode=webrtc`}
              className="w-full h-full border-0"
              allow="autoplay; fullscreen"
              title={expandedCam.name}
            />
          </div>
        </div>

        {/* Right: Camera Thumbnails */}
        <div className="w-[280px] flex flex-col gap-2 overflow-y-auto">
          <h3 className="text-sm font-semibold text-zinc-300 mb-2">Danh sách camera</h3>
          {cameras.map((cam) => (
            <button
              key={cam.id}
              onClick={() => setExpandedCam(cam)}
              className={`p-3 rounded-lg border text-left transition-colors ${
                cam.id === expandedCam.id
                  ? "bg-zinc-800 border-blue-500/50"
                  : "bg-zinc-900 border-zinc-800 hover:bg-zinc-800"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${cam.status === "online" ? "bg-emerald-500" : "bg-zinc-600"}`}
                />
                <span className="text-sm text-zinc-200">{cam.name}</span>
              </div>
              <span className="text-[11px] text-zinc-500 mt-1 block">{cam.location}</span>
            </button>
          ))}
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
        {displayCameras.map((cam) => (
          <div
            key={cam.id}
            onClick={() => cam.status === "online" && setExpandedCam(cam)}
            className="cursor-pointer"
          >
            <CameraTile
              name={cam.name}
              status={cam.status as "online" | "offline"}
              streamUrl={
                cam.status === "online"
                  ? `${GO2RTC_BASE}/stream.html?src=${cam.stream_id}&mode=webrtc`
                  : undefined
              }
              aiTags={cam.ai_features}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
