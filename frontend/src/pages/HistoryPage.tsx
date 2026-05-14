import { useState, useEffect, useCallback } from "react";
import api from "@/api/client";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Search,
  ChevronLeft,
  ChevronRight,
  Users,
  Car,
  Camera,
  Loader2,
} from "lucide-react";

interface Detection {
  id: string;
  type: "person" | "vehicle";
  camera: string;
  timestamp: string;
  attributes: string[];
  confidence: number;
}

const typeConfig = {
  person: { icon: Users, color: "text-blue-400", bg: "bg-blue-500/10", label: "Người" },
  vehicle: { icon: Car, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Phương tiện" },
};

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState("all");
  const [search, setSearch] = useState("");
  const [cameraFilter, setCameraFilter] = useState<string | null>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [cameras, setCameras] = useState<{ camera_id: string; name: string }[]>([]);
  const itemsPerPage = 20;

  useEffect(() => {
    api.get("/cameras").then((res) => {
      const list = res.data.cameras || res.data.data || [];
      setCameras(Array.isArray(list) ? list : []);
    }).catch(() => {});
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const results: Detection[] = [];
      let totalCount = 0;
      const camParam = cameraFilter && cameraFilter !== "all" ? cameraFilter : undefined;

      if (activeTab === "all" || activeTab === "person") {
        const res = await api.get("/persons", {
          params: { page: currentPage, per_page: itemsPerPage, camera_id: camParam },
        });
        const persons = (res.data.persons || []).map((p: Record<string, unknown>) => ({
          id: `p_${p.id}`,
          type: "person" as const,
          camera: String(p.camera_id || ""),
          timestamp: p.timestamp ? new Date(String(p.timestamp)).toLocaleString("vi-VN") : "",
          attributes: [
            ...(p.shirt_colors && Array.isArray(p.shirt_colors) ? p.shirt_colors.map((c: Record<string, string>) => `Áo: ${c.name || ""}`) : []),
            ...(p.pants_colors && Array.isArray(p.pants_colors) ? p.pants_colors.map((c: Record<string, string>) => `Quần: ${c.name || ""}`) : []),
            p.track_id ? `Track #${p.track_id}` : "",
          ].filter(Boolean),
          confidence: Math.round((Number(p.confidence) || 0) * 100),
        }));
        results.push(...persons);
        totalCount += res.data.total || 0;
      }

      if (activeTab === "all" || activeTab === "vehicle") {
        const res = await api.get("/vehicles", {
          params: { page: currentPage, per_page: itemsPerPage, camera_id: camParam },
        });
        const vehicles = (res.data.vehicles || []).map((v: Record<string, unknown>) => ({
          id: `v_${v.id}`,
          type: "vehicle" as const,
          camera: String(v.camera_id || ""),
          timestamp: v.timestamp ? new Date(String(v.timestamp)).toLocaleString("vi-VN") : "",
          attributes: [
            String(v.vehicle_type || "unknown"),
            v.license_plate ? String(v.license_plate) : "",
            v.track_id ? `Track #${v.track_id}` : "",
          ].filter(Boolean),
          confidence: Math.round((Number(v.confidence) || 0) * 100),
        }));
        results.push(...vehicles);
        totalCount += res.data.total || 0;
      }

      // Sort by timestamp desc
      results.sort((a, b) => (b.timestamp > a.timestamp ? 1 : -1));
      setDetections(results);
      setTotal(totalCount);
    } catch (err) {
      console.warn("History fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, currentPage, cameraFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Reset page on filter change
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab, cameraFilter, search]);

  const filtered = search
    ? detections.filter(
        (d) =>
          d.camera.toLowerCase().includes(search.toLowerCase()) ||
          d.attributes.some((a) => a.toLowerCase().includes(search.toLowerCase()))
      )
    : detections;

  const totalPages = Math.max(1, Math.ceil(total / itemsPerPage));

  return (
    <div className="flex flex-col gap-6">
      {/* Filter Bar */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input
            placeholder="Tìm kiếm (biển số, đặc điểm...)"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-500"
          />
        </div>
        <Select value={cameraFilter} onValueChange={setCameraFilter}>
          <SelectTrigger className="w-[220px] bg-zinc-900 border-zinc-800 text-zinc-300">
            <SelectValue placeholder="Camera" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-800">
            <SelectItem value="all">Tất cả camera</SelectItem>
            {cameras.map((c) => (
              <SelectItem key={c.camera_id} value={c.camera_id}>
                {c.camera_id} - {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {loading && <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Tất cả ({total})
          </TabsTrigger>
          <TabsTrigger value="person" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <Users className="h-4 w-4 mr-1.5" />
            Người
          </TabsTrigger>
          <TabsTrigger value="vehicle" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <Car className="h-4 w-4 mr-1.5" />
            Phương tiện
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Data Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-zinc-900">
              <TableHead className="text-zinc-400 w-12">#</TableHead>
              <TableHead className="text-zinc-400">Loại</TableHead>
              <TableHead className="text-zinc-400">Camera</TableHead>
              <TableHead className="text-zinc-400">Thời gian</TableHead>
              <TableHead className="text-zinc-400">Đặc điểm</TableHead>
              <TableHead className="text-zinc-400">Độ tin cậy</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 && !loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-zinc-500 py-12">
                  Không có dữ liệu
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((det, idx) => {
                const config = typeConfig[det.type];
                const Icon = config.icon;
                return (
                  <TableRow key={det.id} className="border-zinc-800 hover:bg-zinc-800/50">
                    <TableCell className="text-zinc-500 text-sm">
                      {(currentPage - 1) * itemsPerPage + idx + 1}
                    </TableCell>
                    <TableCell>
                      <Badge className={`${config.bg} ${config.color} border-transparent text-[11px]`}>
                        <Icon className="h-3 w-3 mr-1" />
                        {config.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-zinc-300 text-sm">
                        <Camera className="h-3.5 w-3.5 text-zinc-500" />
                        {det.camera}
                      </div>
                    </TableCell>
                    <TableCell className="text-zinc-400 text-sm font-mono">
                      {det.timestamp}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1.5 flex-wrap">
                        {det.attributes.map((attr) => (
                          <Badge
                            key={attr}
                            variant="secondary"
                            className="bg-zinc-800 text-zinc-300 border-zinc-700 text-[11px]"
                          >
                            {attr}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              det.confidence >= 90
                                ? "bg-emerald-500"
                                : det.confidence >= 70
                                  ? "bg-amber-500"
                                  : "bg-red-500"
                            }`}
                            style={{ width: `${det.confidence}%` }}
                          />
                        </div>
                        <span className="text-[11px] text-zinc-400 font-mono">
                          {det.confidence}%
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-500">
            Trang {currentPage} / {totalPages} — {total} kết quả
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
              className="border-zinc-800 text-zinc-400 hover:text-white disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
              className="border-zinc-800 text-zinc-400 hover:text-white disabled:opacity-30"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
