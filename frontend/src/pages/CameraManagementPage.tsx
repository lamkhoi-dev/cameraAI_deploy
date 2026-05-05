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

interface Camera {
  id: number;
  name: string;
  location: string;
  ip_address: string;
  status: string;
  brand: string;
  stream_id: string;
  rtsp_url: string;
  ai_features: string[];
}

export default function CameraManagementPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState<Camera | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    location: "",
    ip_address: "",
    rtsp_url: "",
    brand: "Hikvision",
    ai_person: true,
    ai_vehicle: true,
    ai_fire: false,
  });

  const fetchCameras = useCallback(async () => {
    try {
      const res = await api.get("/cameras");
      setCameras(res.data);
    } catch {
      setCameras([
        { id: 1, name: "Sảnh A / Tầng 1", location: "Sảnh A", ip_address: "192.168.1.101", status: "online", brand: "Hikvision", stream_id: "cam_01", rtsp_url: "rtsp://admin:pass@192.168.1.101:554/stream1", ai_features: ["Người", "Xe"] },
        { id: 2, name: "Bãi xe B1", location: "Bãi xe", ip_address: "192.168.1.102", status: "online", brand: "Dahua", stream_id: "cam_02", rtsp_url: "rtsp://admin:pass@192.168.1.102:554/stream1", ai_features: ["Xe"] },
        { id: 3, name: "Hành lang C", location: "Hành lang", ip_address: "192.168.1.103", status: "online", brand: "Hikvision", stream_id: "cam_03", rtsp_url: "rtsp://admin:pass@192.168.1.103:554/stream1", ai_features: ["Người"] },
        { id: 4, name: "Kho Hàng / Tầng 2", location: "Kho hàng", ip_address: "192.168.1.104", status: "offline", brand: "Other", stream_id: "cam_04", rtsp_url: "", ai_features: [] },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const filtered = cameras.filter((cam) => {
    const matchSearch =
      cam.name.toLowerCase().includes(search.toLowerCase()) ||
      cam.ip_address.includes(search);
    const matchStatus = !statusFilter || statusFilter === "all" || cam.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const openAddDialog = () => {
    setEditingCamera(null);
    setFormData({
      name: "",
      location: "",
      ip_address: "",
      rtsp_url: "",
      brand: "Hikvision",
      ai_person: true,
      ai_vehicle: true,
      ai_fire: false,
    });
    setDialogOpen(true);
  };

  const openEditDialog = (cam: Camera) => {
    setEditingCamera(cam);
    setFormData({
      name: cam.name,
      location: cam.location,
      ip_address: cam.ip_address,
      rtsp_url: cam.rtsp_url,
      brand: cam.brand,
      ai_person: cam.ai_features.includes("Người"),
      ai_vehicle: cam.ai_features.includes("Xe"),
      ai_fire: cam.ai_features.includes("Lửa"),
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingCamera) {
        await api.put(`/cameras/${editingCamera.id}`, formData);
      } else {
        await api.post("/cameras", formData);
      }
      fetchCameras();
    } catch {
      // Silently handle if API not available
    }
    setDialogOpen(false);
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/cameras/${id}`);
      fetchCameras();
    } catch {
      setCameras((prev) => prev.filter((c) => c.id !== id));
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
                  <Label className="text-zinc-300">Tên camera</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData((s) => ({ ...s, name: e.target.value }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    placeholder="Sảnh A / Tầng 1"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Vị trí</Label>
                  <Input
                    value={formData.location}
                    onChange={(e) => setFormData((s) => ({ ...s, location: e.target.value }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    placeholder="Sảnh A"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <Label className="text-zinc-300">Địa chỉ IP</Label>
                  <Input
                    value={formData.ip_address}
                    onChange={(e) => setFormData((s) => ({ ...s, ip_address: e.target.value }))}
                    className="bg-zinc-950 border-zinc-700 text-white"
                    placeholder="192.168.1.101"
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
                <Label className="text-zinc-300">RTSP URL</Label>
                <Input
                  value={formData.rtsp_url}
                  onChange={(e) => setFormData((s) => ({ ...s, rtsp_url: e.target.value }))}
                  className="bg-zinc-950 border-zinc-700 text-white"
                  placeholder="rtsp://admin:pass@192.168.1.101:554/stream1"
                />
              </div>
              {/* AI Feature Toggles */}
              <div className="border-t border-zinc-800 pt-4">
                <Label className="text-zinc-300 mb-3 block">AI Layers</Label>
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-200">Nhận diện người</span>
                    <Switch
                      checked={formData.ai_person}
                      onCheckedChange={(v) => setFormData((s) => ({ ...s, ai_person: v }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-200">Nhận diện xe</span>
                    <Switch
                      checked={formData.ai_vehicle}
                      onCheckedChange={(v) => setFormData((s) => ({ ...s, ai_vehicle: v }))}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-200">Phát hiện lửa/khói</span>
                    <Switch
                      checked={formData.ai_fire}
                      onCheckedChange={(v) => setFormData((s) => ({ ...s, ai_fire: v }))}
                    />
                  </div>
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
              <TableHead className="text-zinc-400">AI Layers</TableHead>
              <TableHead className="text-zinc-400 text-right">Hành động</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((cam) => (
              <TableRow key={cam.id} className="border-zinc-800 hover:bg-zinc-800/50">
                <TableCell className="font-medium text-zinc-100">
                  {cam.name}
                </TableCell>
                <TableCell className="text-zinc-400">{cam.location}</TableCell>
                <TableCell className="text-zinc-400 font-mono text-sm">
                  {cam.ip_address}
                </TableCell>
                <TableCell>
                  {cam.status === "online" ? (
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
                  <div className="flex gap-1.5">
                    {cam.ai_features.map((f) => (
                      <Badge
                        key={f}
                        variant="secondary"
                        className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-[11px]"
                      >
                        {f}
                      </Badge>
                    ))}
                  </div>
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
                        onClick={() => handleDelete(cam.id)}
                        className="text-red-400 focus:bg-red-500/10 focus:text-red-400"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Xóa
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
