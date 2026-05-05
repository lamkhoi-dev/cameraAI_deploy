import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { StatCard } from "@/components/StatCard";
import { CameraTile } from "@/components/CameraTile";
import { AlertItem, type AlertItemData } from "@/components/AlertItem";
import { Switch } from "@/components/ui/switch";
import {
  Video,
  Users,
  Car,
  AlertTriangle,
  LayoutGrid,
  Rows3,
  PersonStanding,
  Flame,
} from "lucide-react";
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

// Demo alerts for initial render
const demoAlerts: AlertItemData[] = [
  { id: "1", type: "fire", title: "Phát hiện khói/lửa", source: "Cam 04 - Kho Hàng", time: "14:30" },
  { id: "2", type: "intrusion", title: "Khu vực hạn chế", source: "Cam 01 - Sảnh A", time: "14:15" },
  { id: "3", type: "info", title: "Hệ thống reboot", source: "Server 02", time: "12:00" },
];

export default function DashboardPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [alerts] = useState<AlertItemData[]>(demoAlerts);
  const [gridLayout, setGridLayout] = useState<"2x2" | "3x3">("2x2");
  const [aiModules, setAiModules] = useState({
    person: true,
    vehicle: true,
    fire: false,
  });

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      setCameras(res.data);
    } catch {
      // Use demo data when API unavailable
      setCameras([
        { id: 1, name: "Sảnh A / Tầng 1", location: "Sảnh A", status: "online", stream_id: "cam_01", ai_features: ["Người"] },
        { id: 2, name: "Bãi xe B1", location: "Bãi xe", status: "online", stream_id: "cam_02", ai_features: ["Xe"] },
        { id: 3, name: "Hành lang C", location: "Hành lang", status: "online", stream_id: "cam_03", ai_features: [] },
        { id: 4, name: "Kho Hàng / Tầng 2", location: "Kho hàng", status: "offline", stream_id: "cam_04", ai_features: [] },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const onlineCameras = cameras.filter((c) => c.status === "online").length;
  const cols = gridLayout === "2x2" ? "grid-cols-2" : "grid-cols-3";
  const displayCameras = gridLayout === "2x2" ? cameras.slice(0, 4) : cameras.slice(0, 9);

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* Left/Center Column */}
      <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2 pb-6">
        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Camera Online"
            value={`${onlineCameras}/${cameras.length}`}
            icon={<Video className="h-5 w-5 text-blue-500" />}
            trend={{ value: "1", up: true }}
            subtitle="Đang hoạt động"
          />
          <StatCard
            label="Người phát hiện"
            value="247"
            icon={<Users className="h-5 w-5 text-blue-500" />}
            subtitle="Hôm nay"
          />
          <StatCard
            label="Phương tiện"
            value="183"
            icon={<Car className="h-5 w-5 text-zinc-400" />}
            subtitle="Hôm nay"
          />
          <StatCard
            label="Cảnh báo"
            value="3"
            icon={<AlertTriangle className="h-5 w-5 text-amber-500" />}
            subtitle="Chưa xử lý"
            subtitleBadge
          />
        </div>

        {/* Camera Grid Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Luồng Live</h2>
          <div className="flex items-center gap-3">
            <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
              <button
                onClick={() => setGridLayout("2x2")}
                className={`px-2 py-1 ${gridLayout === "2x2" ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setGridLayout("3x3")}
                className={`px-2 py-1 ${gridLayout === "3x3" ? "bg-zinc-800 text-zinc-100" : "text-zinc-500 hover:text-zinc-300"}`}
              >
                <Rows3 className="h-4 w-4" />
              </button>
            </div>
            <Link
              to="/live"
              className="px-3 py-1.5 border border-zinc-800 rounded-lg text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
            >
              Xem tất cả
            </Link>
          </div>
        </div>

        {/* Camera Grid */}
        <div className={`grid ${cols} gap-4 flex-1 min-h-[400px]`}>
          {displayCameras.map((cam) => (
            <CameraTile
              key={cam.id}
              name={cam.name}
              status={cam.status as "online" | "offline"}
              streamUrl={
                cam.status === "online"
                  ? `${GO2RTC_BASE}/stream.html?src=${cam.stream_id}&mode=webrtc`
                  : undefined
              }
              aiTags={cam.ai_features}
            />
          ))}
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-[300px] flex flex-col gap-6 flex-shrink-0">
        {/* Alert Feed */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col h-[55%] overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-800 flex justify-between items-center bg-zinc-900">
            <h3 className="text-sm font-semibold text-white">Cảnh báo gần đây</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-2">
            {alerts.map((alert) => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </div>
        </div>

        {/* AI Status Toggles */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col flex-1 overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-800 bg-zinc-900">
            <h3 className="text-sm font-semibold text-white">Module AI</h3>
          </div>
          <div className="p-4 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <PersonStanding className="h-5 w-5 text-zinc-400" />
                <span className="text-sm text-zinc-200">Nhận diện người</span>
              </div>
              <Switch
                checked={aiModules.person}
                onCheckedChange={(v) => setAiModules((s) => ({ ...s, person: v }))}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Car className="h-5 w-5 text-zinc-400" />
                <span className="text-sm text-zinc-200">Nhận diện xe</span>
              </div>
              <Switch
                checked={aiModules.vehicle}
                onCheckedChange={(v) => setAiModules((s) => ({ ...s, vehicle: v }))}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Flame className="h-5 w-5 text-zinc-400" />
                <span className="text-sm text-zinc-200">Phát hiện lửa/khói</span>
              </div>
              <Switch
                checked={aiModules.fire}
                onCheckedChange={(v) => setAiModules((s) => ({ ...s, fire: v }))}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
