import { useState, useEffect, useCallback } from "react";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Camera,
  Cpu,
  Loader2,
  CheckCircle2,
  MapPin,
} from "lucide-react";
import api from "@/api/client";

interface CameraAI {
  id: number;
  camera_id: string;
  name: string;
  location: string;
  is_active: boolean;
  connection_status: string;
  ai_detect_person: boolean;
  ai_detect_vehicle: boolean;
  ai_detect_fire: boolean;
}

export default function SettingsPage() {
  const [cameras, setCameras] = useState<CameraAI[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [maxAiCameras, setMaxAiCameras] = useState(12);

  const fetchCameras = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get("/cameras?per_page=100");
      const list = res.data.cameras || res.data.data || res.data;
      setCameras(Array.isArray(list) ? list : []);
    } catch (err) {
      console.warn("Failed to fetch cameras:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const aiActiveCount = cameras.filter(
    (c) => c.ai_detect_person || c.ai_detect_vehicle || c.ai_detect_fire
  ).length;

  const toggleAI = async (
    cameraId: string,
    field: "detect_person" | "detect_vehicle" | "detect_fire",
    value: boolean
  ) => {
    // Check max limit when enabling
    if (value) {
      const cam = cameras.find((c) => c.camera_id === cameraId);
      if (cam) {
        const currentlyHasAI = cam.ai_detect_person || cam.ai_detect_vehicle || cam.ai_detect_fire;
        if (!currentlyHasAI && aiActiveCount >= maxAiCameras) {
          alert(`Đã đạt giới hạn ${maxAiCameras} camera AI. Vui lòng tắt AI ở camera khác trước.`);
          return;
        }
      }
    }

    setSaving(cameraId);
    try {
      await api.patch(`/cameras/${cameraId}/ai-layers`, {
        [field]: value,
      });
      setCameras((prev) =>
        prev.map((c) => {
          if (c.camera_id !== cameraId) return c;
          const key = field === "detect_person" ? "ai_detect_person"
            : field === "detect_vehicle" ? "ai_detect_vehicle"
            : "ai_detect_fire";
          return { ...c, [key]: value };
        })
      );
      setSaved(cameraId);
      setTimeout(() => setSaved(null), 1500);
    } catch (err) {
      console.error("Failed to toggle AI:", err);
    } finally {
      setSaving(null);
    }
  };

  const hasAnyAI = (c: CameraAI) => c.ai_detect_person || c.ai_detect_vehicle || c.ai_detect_fire;

  return (
    <div className="space-y-6 h-[calc(100vh-7rem)] overflow-y-auto pr-2 pb-6">
      {/* Header stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-center justify-center">
            <Camera className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{cameras.length}</p>
            <p className="text-xs text-zinc-500">Tổng Camera</p>
          </div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-center">
            <Cpu className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">
              <span className={aiActiveCount >= maxAiCameras ? "text-amber-400" : "text-emerald-400"}>
                {aiActiveCount}
              </span>
              <span className="text-zinc-500 text-lg">/{maxAiCameras}</span>
            </p>
            <p className="text-xs text-zinc-500">AI Active</p>
          </div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-zinc-800 border border-zinc-700 rounded-lg flex items-center justify-center">
            <Cpu className="h-5 w-5 text-zinc-400" />
          </div>
          <div className="flex-1">
            <p className="text-xs text-zinc-500 mb-1">Giới hạn AI</p>
            <Input
              type="number"
              value={maxAiCameras}
              onChange={(e) => setMaxAiCameras(Math.max(1, Math.min(cameras.length, Number(e.target.value) || 1)))}
              className="h-8 w-20 bg-zinc-800 border-zinc-700 text-white text-sm"
              min={1}
              max={cameras.length || 25}
            />
          </div>
        </div>
      </div>

      {/* Camera AI Config Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Cpu className="h-4 w-4 text-zinc-400" />
            Cấu hình AI theo Camera
          </h3>
          <span className="text-xs text-zinc-500">
            {aiActiveCount >= maxAiCameras ? "⚠ Đã đạt giới hạn" : `Còn ${maxAiCameras - aiActiveCount} slot`}
          </span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 text-zinc-500 animate-spin" />
          </div>
        ) : (
          <div className="divide-y divide-zinc-800/50">
            {/* Table Header */}
            <div className="grid grid-cols-[1fr_80px_80px_80px_100px] gap-4 px-4 py-2 bg-zinc-950/50">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">Camera</span>
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium text-center">Người</span>
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium text-center">Xe</span>
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium text-center">Lửa</span>
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium text-center">Trạng thái</span>
            </div>

            {cameras.map((cam) => (
              <div
                key={cam.camera_id}
                className="grid grid-cols-[1fr_80px_80px_80px_100px] gap-4 px-4 py-3 items-center hover:bg-zinc-800/30 transition-colors"
              >
                {/* Camera info */}
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cam.is_active ? "bg-emerald-500" : "bg-zinc-600"}`} />
                  <div className="min-w-0">
                    <p className="text-sm text-zinc-200 font-medium truncate">{cam.name}</p>
                    <p className="text-[11px] text-zinc-500 truncate flex items-center gap-1">
                      <MapPin className="h-3 w-3 inline" /> {cam.location}
                    </p>
                  </div>
                </div>

                {/* Person toggle */}
                <div className="flex justify-center">
                  <Switch
                    checked={cam.ai_detect_person}
                    onCheckedChange={(v) => toggleAI(cam.camera_id, "detect_person", v)}
                    disabled={saving === cam.camera_id}
                  />
                </div>

                {/* Vehicle toggle */}
                <div className="flex justify-center">
                  <Switch
                    checked={cam.ai_detect_vehicle}
                    onCheckedChange={(v) => toggleAI(cam.camera_id, "detect_vehicle", v)}
                    disabled={saving === cam.camera_id}
                  />
                </div>

                {/* Fire toggle */}
                <div className="flex justify-center">
                  <Switch
                    checked={cam.ai_detect_fire}
                    onCheckedChange={(v) => toggleAI(cam.camera_id, "detect_fire", v)}
                    disabled={saving === cam.camera_id}
                  />
                </div>

                {/* Status */}
                <div className="flex justify-center">
                  {saving === cam.camera_id ? (
                    <Loader2 className="h-4 w-4 text-zinc-500 animate-spin" />
                  ) : saved === cam.camera_id ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : hasAnyAI(cam) ? (
                    <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px]">
                      AI Active
                    </Badge>
                  ) : (
                    <Badge className="bg-zinc-800 text-zinc-500 border-zinc-700 text-[10px]">
                      Off
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
