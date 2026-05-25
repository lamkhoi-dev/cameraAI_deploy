import { useState, useEffect, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { RegionEditor } from "@/components/RegionEditor";
import {
  Plus,
  Search,
  MoreVertical,
  Pencil,
  Trash2,
  Wifi,
  WifiOff,
} from "lucide-react";
import api from "@/api/client";

// Backend Camera model
interface BackendCamera {
  id: number;
  camera_id: string;
  name: string;
  location: string;
  stream_url: string;
  protocol: string;
  resolution: string | null;
  fps: number;
  brand: string | null;
  model: string | null;
  is_active: boolean;
  connection_status: string;
  ai_detect_person: boolean;
  ai_detect_vehicle: boolean;
  ai_detect_fire: boolean;
  ai_processing_fps?: number;
  monitoring_interval_minutes?: number;
  ai_region_points?: number[][] | null;
  patrol_region_points?: number[][] | null;
  username: string | null;
  password: string | null;
  notes: string | null;
  display_interval_seconds?: number;
  fallback_seconds?: number;
}

// Extract IP from RTSP URL
function extractIp(streamUrl: string): string {
  try {
    const match = streamUrl.match(/@([\d.]+)/);
    if (match) return match[1];
    const urlMatch = streamUrl.match(/:\/\/([\d.]+)/);
    if (urlMatch) return urlMatch[1];
  } catch { /* ignore */ }
  return "—";
}

function getStatus(cam: BackendCamera): "online" | "offline" {
  return cam.is_active ? "online" : "offline";
}

export default function CameraManagementPage() {
  const [cameras, setCameras] = useState<BackendCamera[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState<BackendCamera | null>(null);
  const [formData, setFormData] = useState({
    camera_id: "",
    name: "",
    location: "",
    stream_url: "",
    brand: "Hikvision",
    ai_detect_person: true,
    ai_detect_vehicle: true,
    ai_detect_fire: false,
    ai_processing_fps: 3,
    monitoring_interval_minutes: 5,
    ai_region_points: [] as number[][],
    patrol_region_points: [] as number[][],
    display_interval_seconds: 5,
    fallback_seconds: 5,
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

  const filtered = cameras.filter((cam) => {
    const ip = extractIp(cam.stream_url);
    const matchSearch =
      cam.name.toLowerCase().includes(search.toLowerCase()) ||
      ip.includes(search) ||
      cam.camera_id.toLowerCase().includes(search.toLowerCase());
    const status = getStatus(cam);
    const matchStatus = !statusFilter || statusFilter === "all" || status === statusFilter;
    return matchSearch && matchStatus;
  });

  const openAddDialog = () => {
    setEditingCamera(null);
    setFormData({
      camera_id: "",
      name: "",
      location: "",
      stream_url: "",
      brand: "Hikvision",
      ai_detect_person: true,
      ai_detect_vehicle: true,
      ai_detect_fire: false,
      ai_processing_fps: 3,
      monitoring_interval_minutes: 5,
      ai_region_points: [],
      patrol_region_points: [],
      display_interval_seconds: 5,
      fallback_seconds: 5,
    });
    setDialogOpen(true);
  };

  const openEditDialog = (cam: BackendCamera) => {
    setEditingCamera(cam);
    setFormData({
      camera_id: cam.camera_id,
      name: cam.name,
      location: cam.location,
      stream_url: cam.stream_url,
      brand: cam.brand || "Hikvision",
      ai_detect_person: cam.ai_detect_person ?? true,
      ai_detect_vehicle: cam.ai_detect_vehicle ?? true,
      ai_detect_fire: cam.ai_detect_fire ?? false,
      ai_processing_fps: cam.ai_processing_fps ?? 3,
      monitoring_interval_minutes: cam.monitoring_interval_minutes ?? 5,
      ai_region_points: cam.ai_region_points ?? [],
      patrol_region_points: cam.patrol_region_points ?? [],
      display_interval_seconds: cam.display_interval_seconds ?? 5,
      fallback_seconds: cam.fallback_seconds ?? 5,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      const payload = {
        camera_id: formData.camera_id,
        name: formData.name,
        location: formData.location,
        stream_url: formData.stream_url,
        brand: formData.brand,
        ai_detect_person: formData.ai_detect_person,
        ai_detect_vehicle: formData.ai_detect_vehicle,
        ai_detect_fire: formData.ai_detect_fire,
        ai_processing_fps: formData.ai_processing_fps,
        monitoring_interval_minutes: formData.monitoring_interval_minutes,
        ai_region_points: formData.ai_region_points,
        patrol_region_points: formData.patrol_region_points,
        display_interval_seconds: formData.display_interval_seconds,
        fallback_seconds: formData.fallback_seconds,
      };

      if (editingCamera) {
        await api.put(`/cameras/${editingCamera.camera_id}`, payload);
      } else {
        await api.post("/cameras", payload);
      }
      fetchCameras();
    } catch {
      // Silently handle if API not available
    }
    setDialogOpen(false);
  };

  const handleDelete = async (cameraId: string) => {
    try {
      await api.delete(`/cameras/${cameraId}`);
      fetchCameras();
    } catch {
      setCameras((prev) => prev.filter((c) => c.camera_id !== cameraId));
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Filter Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <Input
              placeholder="Tìm camera..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-500"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[150px] bg-zinc-900 border-zinc-800 text-zinc-300">
              <SelectValue placeholder="Trạng thái" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="all">Tất cả</SelectItem>
              <SelectItem value="online">Online</SelectItem>
              <SelectItem value="offline">Offline</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button
          onClick={openAddDialog}
          className="bg-blue-600 hover:bg-blue-500 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Thêm camera
        </Button>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="bg-zinc-900 border-zinc-800 text-white max-w-lg">
            <DialogHeader>
              <DialogTitle>
                {editingCamera ? "Chỉnh sửa camera" : "Thêm camera mới"}
              </DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Camera ID</Label>
                  <Input
                    value={formData.camera_id}
                    onChange={(e) => setFormData((s) => ({ ...s, camera_id: e.target.value }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    placeholder="cam_01"
                    disabled={!!editingCamera}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Tên camera</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData((s) => ({ ...s, name: e.target.value }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    placeholder="Sảnh A / Tầng 1"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Vị trí</Label>
                  <Input
                    value={formData.location}
                    onChange={(e) => setFormData((s) => ({ ...s, location: e.target.value }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    placeholder="Sảnh A"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Hãng</Label>
                  <Select
                    value={formData.brand}
                    onValueChange={(v: string | null) => setFormData((s) => ({ ...s, brand: v || "Hikvision" }))}
                  >
                    <SelectTrigger className="bg-zinc-950 border-zinc-700 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="Hikvision">Hikvision</SelectItem>
                      <SelectItem value="Dahua">Dahua</SelectItem>
                      <SelectItem value="Other">Khác</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <Label className="text-zinc-300">Stream URL (RTSP)</Label>
                <Input
                  value={formData.stream_url}
                  onChange={(e) => setFormData((s) => ({ ...s, stream_url: e.target.value }))}
                  className="bg-zinc-950 border-zinc-700 text-white"
                  placeholder="rtsp://admin:pass@192.168.1.101:554/stream1"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">FPS xử lý AI</Label>
                  <Input
                    type="number"
                    value={formData.ai_processing_fps}
                    onChange={(e) => setFormData((s) => ({ ...s, ai_processing_fps: Number(e.target.value) }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    min={1}
                    max={30}
                  />
                  <p className="text-[11px] text-zinc-500">Ví dụ: 3, 5, 7 FPS cho FaceID / biển số / khói lửa.</p>
                </div>
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Chu kỳ giám sát (phút)</Label>
                  <Input
                    type="number"
                    value={formData.monitoring_interval_minutes}
                    onChange={(e) => setFormData((s) => ({ ...s, monitoring_interval_minutes: Number(e.target.value) }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    min={1}
                    max={60}
                  />
                  <p className="text-[11px] text-zinc-500">Ví dụ: 5, 10, 15 phút/lần cho người và phương tiện.</p>
                </div>
              </div>
              <div className="border border-zinc-800 rounded-xl p-3 bg-zinc-950/50">
                <div className="mb-4">
                  <p className="text-sm font-medium text-zinc-200">Vùng AI xử lý realtime</p>
                  <p className="text-xs text-zinc-500">Dùng cho FaceID, biển số, khói/lửa.</p>
                </div>
                <RegionEditor
                  value={(formData.ai_region_points || []) as [number, number][]}
                  onChange={(next) => setFormData((s) => ({ ...s, ai_region_points: next }))}
                  cameraId={editingCamera ? formData.camera_id : undefined}
                />
              </div>
              <div className="border border-zinc-800 rounded-xl p-3 bg-zinc-950/50">
                <div className="mb-4">
                  <p className="text-sm font-medium text-zinc-200">Vùng AI tuần tra</p>
                  <p className="text-xs text-zinc-500">Dùng cho giám sát định kỳ người và phương tiện.</p>
                </div>
                <RegionEditor
                  value={(formData.patrol_region_points || []) as [number, number][]}
                  onChange={(next) => setFormData((s) => ({ ...s, patrol_region_points: next }))}
                  cameraId={editingCamera ? formData.camera_id : undefined}
                />
              </div>
              {/* AI Detection Toggle */}
              <div className="border-t border-zinc-800 pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-200">Bật AI Detection</span>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-zinc-200">Person</span>
                      <Switch
                        checked={formData.ai_detect_person}
                        onCheckedChange={(v) => setFormData((s) => ({ ...s, ai_detect_person: v }))}
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-zinc-200">Vehicle</span>
                      <Switch
                        checked={formData.ai_detect_vehicle}
                        onCheckedChange={(v) => setFormData((s) => ({ ...s, ai_detect_vehicle: v }))}
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-zinc-200">Fire</span>
                      <Switch
                        checked={formData.ai_detect_fire}
                        onCheckedChange={(v) => setFormData((s) => ({ ...s, ai_detect_fire: v }))}
                      />
                    </div>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Thời gian hiển thị (giây)</Label>
                  <Input
                    type="number"
                    value={formData.display_interval_seconds}
                    onChange={(e) => setFormData((s) => ({ ...s, display_interval_seconds: Number(e.target.value) }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    min={1}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Thời gian lấp bù (giây)</Label>
                  <Input
                    type="number"
                    value={formData.fallback_seconds}
                    onChange={(e) => setFormData((s) => ({ ...s, fallback_seconds: Number(e.target.value) }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    min={1}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDialogOpen(false)}
                className="border-zinc-700 text-zinc-300"
              >
                Hủy
              </Button>
              <Button
                onClick={handleSave}
                className="bg-blue-600 hover:bg-blue-500 text-white"
              >
                {editingCamera ? "Cập nhật" : "Thêm camera"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Camera Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-zinc-900">
              <TableHead className="text-zinc-400">Tên camera</TableHead>
              <TableHead className="text-zinc-400">Vị trí</TableHead>
              <TableHead className="text-zinc-400">IP</TableHead>
              <TableHead className="text-zinc-400">Trạng thái</TableHead>
              <TableHead className="text-zinc-400">AI Detection</TableHead>
              <TableHead className="text-zinc-400 text-right">Hành động</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((cam) => {
              const status = getStatus(cam);
              return (
                <TableRow key={cam.camera_id} className="border-zinc-800 hover:bg-zinc-800/50">
                  <TableCell className="font-medium text-zinc-100">
                    {cam.name}
                  </TableCell>
                  <TableCell className="text-zinc-400">{cam.location}</TableCell>
                  <TableCell className="text-zinc-400 font-mono text-sm">
                    {extractIp(cam.stream_url)}
                  </TableCell>
                  <TableCell>
                    {status === "online" ? (
                      <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20">
                        <Wifi className="h-3 w-3 mr-1" />
                        Online
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="bg-zinc-800 text-zinc-500 border-zinc-700">
                        <WifiOff className="h-3 w-3 mr-1" />
                        Offline
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {(cam.ai_detect_person || cam.ai_detect_vehicle) ? (
                      <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-[11px]">
                        AI Active
                      </Badge>
                    ) : (
                      <span className="text-zinc-600 text-sm">Tắt</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-md text-sm font-medium text-zinc-400 hover:text-white h-9 w-9">
                        <MoreVertical className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent className="bg-zinc-900 border-zinc-800" align="end">
                        <DropdownMenuItem
                          onClick={() => openEditDialog(cam)}
                          className="text-zinc-300 focus:bg-zinc-800 focus:text-white"
                        >
                          <Pencil className="h-4 w-4 mr-2" />
                          Chỉnh sửa
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleDelete(cam.camera_id)}
                          className="text-red-400 focus:bg-red-500/10 focus:text-red-400"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Xóa
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
