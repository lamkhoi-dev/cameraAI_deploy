import { useState, useEffect, useCallback, useMemo } from "react";
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
import { useSocket } from "@/hooks/useSocket";

// Same-origin proxy via nginx — no cross-origin issues
const GO2RTC_BASE = import.meta.env.VITE_GO2RTC_BASE || "/go2rtc";

// Backend Camera model shape
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

interface Stats {
  total_persons: number;
  total_vehicles: number;
  active_alerts: number;
  total_alerts: number;
  recent_alerts: AlertItemData[];
}

export default function DashboardPage() {
  const [cameras, setCameras] = useState<BackendCamera[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [alerts, setAlerts] = useState<AlertItemData[]>([]);
  const [gridLayout, setGridLayout] = useState<"2x2" | "3x3">("2x2");
  const [aiModules, setAiModules] = useState({
    person: true,
    vehicle: true,
    fire: false,
  });

  // Socket.IO: real-time events
  const socketEvents = useMemo(
    () => ({
      new_alert: (data: unknown) => {
        const alert = data as AlertItemData;
        setAlerts((prev) => [alert, ...prev].slice(0, 20));
      },
    }),
    []
  );

  useSocket({
    rooms: ["alerts", "persons", "vehicles"],
    events: socketEvents,
  });

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      // FastAPI returns { cameras: [...] }, Flask returns { data: [...] }
      const list = res.data.cameras || res.data.data || res.data;
      setCameras(Array.isArray(list) ? list : []);
    } catch (err) {
      console.warn("Failed to fetch cameras:", err);
      setCameras([]);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get("/statistics");
      setStats(res.data);
      // Map recent_alerts to AlertItemData
      if (res.data.recent_alerts) {
        setAlerts(
          res.data.recent_alerts.map((a: Record<string, string>) => ({
            id: String(a.id),
            type: a.alert_type === "fire" ? "fire" : a.severity === "high" ? "intrusion" : "info",
            title: a.description || a.alert_type,
            source: a.location || "Unknown",
            time: a.timestamp ? new Date(a.timestamp).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) : "",
          }))
        );
      }
    } catch {
      // Demo stats when API unavailable
      setStats({ total_persons: 247, total_vehicles: 183, active_alerts: 3, total_alerts: 15, recent_alerts: [] });
      setAlerts([
        { id: "1", type: "fire", title: "Phát hiện khói/lửa", source: "Cam 04 - Kho Hàng", time: "14:30" },
        { id: "2", type: "intrusion", title: "Khu vực hạn chế", source: "Cam 01 - Sảnh A", time: "14:15" },
        { id: "3", type: "info", title: "Hệ thống reboot", source: "Server 02", time: "12:00" },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
    fetchStats();
  }, [fetchCameras, fetchStats]);

  // Map backend status to UI status
  const getStatus = (cam: BackendCamera): "online" | "offline" =>
    cam.is_active && cam.last_connection_status === "connected" ? "online" : "offline";

  const getAiTags = (cam: BackendCamera): string[] =>
    cam.enable_detection ? ["AI Active"] : [];

  const onlineCameras = cameras.filter((c) => getStatus(c) === "online").length;
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
            value={String(stats?.total_persons ?? 0)}
            icon={<Users className="h-5 w-5 text-blue-500" />}
            subtitle="Tổng cộng"
          />
          <StatCard
            label="Phương tiện"
            value={String(stats?.total_vehicles ?? 0)}
            icon={<Car className="h-5 w-5 text-zinc-400" />}
            subtitle="Tổng cộng"
          />
          <StatCard
            label="Cảnh báo"
            value={String(stats?.active_alerts ?? 0)}
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
              key={cam.camera_id}
              name={cam.name}
              status={getStatus(cam)}
              streamUrl={
                getStatus(cam) === "online"
                  ? `${GO2RTC_BASE}/stream.html?src=${cam.camera_id}&mode=webrtc,mse`
                  : undefined
              }
              resolution={cam.resolution || "1080P / 30FPS"}
              aiTags={getAiTags(cam)}
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
