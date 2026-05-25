import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { StatCard } from "@/components/StatCard";
import { CameraTile } from "@/components/CameraTile";
import { AlertItem, type AlertItemData } from "@/components/AlertItem";
import {
  Video,
  Users,
  Car,
  AlertTriangle,
  LayoutGrid,
  Rows3,
  Cpu,
} from "lucide-react";
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
  const [cameraEvents, setCameraEvents] = useState<Record<string, { persons: number; vehicles: number }>>({});

  // Track event counts per camera
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
      const msg = data as { type?: string; payload?: AlertItemData & { camera_id?: string; count?: number } };

      if (msg.type === "new_alert" && msg.payload) {
        setAlerts((prev) => [msg.payload!, ...prev].slice(0, 20));
      }

      if (msg.type === "new_person_detected" && msg.payload?.camera_id) {
        const camId = msg.payload.camera_id;
        const windowMs = getEventWindowMs(camId);
        setCameraEvents((prev) => ({
          ...prev,
          [camId]: {
            persons: (prev[camId]?.persons || 0) + (msg.payload!.count || 1),
            vehicles: prev[camId]?.vehicles || 0,
          },
        }));
        clearTimeout(eventTimers.current[camId]);
        eventTimers.current[camId] = setTimeout(() => {
          setCameraEvents((prev) => {
            const next = { ...prev };
            delete next[camId];
            return next;
          });
        }, windowMs);
      }

      if (msg.type === "new_vehicle_detected" && msg.payload?.camera_id) {
        const camId = msg.payload.camera_id;
        const windowMs = getEventWindowMs(camId);
        setCameraEvents((prev) => ({
          ...prev,
          [camId]: {
            persons: prev[camId]?.persons || 0,
            vehicles: (prev[camId]?.vehicles || 0) + (msg.payload!.count || 1),
          },
        }));
        clearTimeout(eventTimers.current[camId]);
        eventTimers.current[camId] = setTimeout(() => {
          setCameraEvents((prev) => {
            const next = { ...prev };
            delete next[camId];
            return next;
          });
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

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get("/statistics");
      setStats(res.data);
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
    } catch (err) {
      console.warn("Stats fetch failed:", err);
      setStats({ total_persons: 0, total_vehicles: 0, active_alerts: 0, total_alerts: 0, recent_alerts: [] });
      setAlerts([]);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
    fetchStats();
  }, [fetchCameras, fetchStats]);

  const getStatus = (cam: BackendCamera): "online" | "offline" =>
    cam.is_active && cam.connection_status === "connected" ? "online" : "offline";

  const getAiTags = (cam: BackendCamera): string[] =>
    cam.ai_detect_person || cam.ai_detect_vehicle ? ["AI"] : [];

  const onlineCameras = cameras.filter((c) => getStatus(c) === "online").length;
  const aiCameras = cameras.filter((c) => c.ai_detect_person || c.ai_detect_vehicle || c.ai_detect_fire).length;
  const cols = gridLayout === "2x2" ? "grid-cols-2" : "grid-cols-3";
  const displayCameras = gridLayout === "2x2" ? cameras.slice(0, 4) : cameras.slice(0, 9);

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* Left/Center Column */}
      <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2 pb-6">
        {/* Stats Row */}
        <div className="grid grid-cols-5 gap-4">
          <StatCard
            label="Camera Online"
            value={`${onlineCameras}/${cameras.length}`}
            icon={<Video className="h-5 w-5 text-blue-500" />}
            subtitle="Đang hoạt động"
          />
          <StatCard
            label="AI Tracking"
            value={`${aiCameras}/${cameras.length}`}
            icon={<Cpu className="h-5 w-5 text-emerald-500" />}
            subtitle="Đang xử lý AI"
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
          <h2 className="text-lg font-semibold text-white">Giám sát Camera</h2>
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
        <div className={`grid ${cols} gap-3 flex-1`}>
          {displayCameras.map((cam) => (
            <CameraTile
              key={cam.camera_id}
              name={cam.name}
              status={getStatus(cam)}
              cameraId={cam.camera_id}
              displayIntervalSeconds={cam.display_interval_seconds}
              resolution={cam.resolution || "1080P / 30FPS"}
              aiTags={getAiTags(cam)}
              events={cameraEvents[cam.camera_id]}
            />
          ))}
        </div>
      </div>

      {/* Right Panel — Alerts only */}
      <div className="w-[300px] flex flex-col gap-6 flex-shrink-0">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col flex-1 overflow-hidden">
          <div className="px-4 py-3 border-b border-zinc-800 flex justify-between items-center bg-zinc-900">
            <h3 className="text-sm font-semibold text-white">Cảnh báo gần đây</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-2">
            {alerts.map((alert) => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
            {alerts.length === 0 && (
              <div className="flex-1 flex items-center justify-center text-zinc-600 text-sm py-8">
                Không có cảnh báo
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
