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
  last_connection_status: string;
  enable_detection: boolean;
  username: string | null;
  password: string | null;
  notes: string | null;
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
    enable_detection: true,
  });

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      const list = res.data.data || res.data;
      setCameras(Array.isArray(list) ? list : []);
    } catch {
      setCameras([
        { id: 1, camera_id: "cam_01", name: "Sảnh A / Tầng 1", location: "Sảnh A", stream_url: "rtsp://admin:pass@192.168.1.101:554/stream1", protocol: "rtsp", resolution: "1920x1080", fps: 30, brand: "Hikvision", model: null, is_active: true, last_connection_status: "connected", enable_detection: true, username: null, password: null, notes: null },
        { id: 2, camera_id: "cam_02", name: "Bãi xe B1", location: "Bãi xe", stream_url: "rtsp://admin:pass@192.168.1.102:554/stream1", protocol: "rtsp", resolution: "1920x1080", fps: 30, brand: "Dahua", model: null, is_active: true, last_connection_status: "connected", enable_detection: true, username: null, password: null, notes: null },
        { id: 3, camera_id: "cam_03", name: "Hành lang C", location: "Hành lang", stream_url: "rtsp://admin:pass@192.168.1.103:554/stream1", protocol: "rtsp", resolution: "1920x1080", fps: 30, brand: "Hikvision", model: null, is_active: true, last_connection_status: "disconnected", enable_detection: true, username: null, password: null, notes: null },
        { id: 4, camera_id: "cam_04", name: "Kho Hàng / Tầng 2", location: "Kho hàng", stream_url: "", protocol: "rtsp", resolution: null, fps: 30, brand: "Other", model: null, is_active: false, last_connection_status: "disconnected", enable_detection: false, username: null, password: null, notes: null },
      ]);
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
      enable_detection: true,
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
      enable_detection: cam.enable_detection,
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
        enable_detection: formData.enable_detection,
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
              {/* AI Detection Toggle */}
              <div className="border-t border-zinc-800 pt-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-200">Bật AI Detection</span>
                  <Switch
                    checked={formData.enable_detection}
                    onCheckedChange={(v) => setFormData((s) => ({ ...s, enable_detection: v }))}
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
                    {cam.enable_detection ? (
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
