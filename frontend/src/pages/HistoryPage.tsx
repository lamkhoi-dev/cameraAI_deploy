import { useState, useEffect, useCallback } from "react";
import api from "@/api/client";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Search, ChevronLeft, ChevronRight, Users, Car, Camera, Loader2,
  LayoutGrid, List, CalendarIcon, SlidersHorizontal, X,
} from "lucide-react";
import { format } from "date-fns";
import { vi } from "date-fns/locale";
import { COLOR_MAP, ALL_COLORS, cropUrl } from "@/lib/colors";
import { formatVN } from "@/lib/date";
import DetectionModal from "@/components/DetectionModal";
import type { DetectionDetail, ColorInfo } from "@/components/DetectionModal";

type ViewMode = "table" | "grid";

const VEHICLE_TYPES = ["car", "motorcycle", "bus", "truck", "bicycle"];

// ─── Color Chip Toggle ──────────────────────────────────────────────
function ColorChip({ name, active, onClick }: { name: string; active: boolean; onClick: () => void }) {
  const hex = COLOR_MAP[name] || "#6B7280";
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] border transition-all cursor-pointer ${
        active ? "border-blue-500 bg-blue-500/10 text-blue-300" : "border-zinc-700 bg-zinc-800/50 text-zinc-400 hover:border-zinc-500"
      }`}
    >
      <span className="w-3 h-3 rounded-full border border-zinc-600" style={{ backgroundColor: hex }} />
      {name}
      {active && <X className="h-3 w-3" />}
    </button>
  );
}

// ─── Detection Card (Grid View) ─────────────────────────────────────
function DetectionCard({ det, onClick }: { det: DetectionDetail; onClick: () => void }) {
  const imgSrc = cropUrl(det.image_path);
  const isPerson = det.type === "person";
  const colors: ColorInfo[] = isPerson ? (det.shirt_colors || []) : (det.vehicle_colors || []);
  const conf = Math.round(det.confidence * 100);

  return (
    <div
      onClick={onClick}
      className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden hover:border-zinc-600 transition-all cursor-pointer group"
    >
      {/* Image */}
      <div className="h-40 bg-zinc-800 relative overflow-hidden">
        {imgSrc ? (
          <img src={imgSrc} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-600">
            {isPerson ? <Users className="h-8 w-8" /> : <Car className="h-8 w-8" />}
          </div>
        )}
        {/* Confidence badge */}
        <div className={`absolute top-2 right-2 px-1.5 py-0.5 rounded text-[10px] font-mono ${
          conf >= 80 ? "bg-emerald-600/80" : conf >= 60 ? "bg-amber-600/80" : "bg-red-600/80"
        } text-white`}>
          {conf}%
        </div>
        {/* Type badge */}
        <Badge className={`absolute top-2 left-2 text-[10px] ${isPerson ? "bg-blue-600/80 text-blue-100" : "bg-emerald-600/80 text-emerald-100"}`}>
          {isPerson ? "Người" : det.vehicle_type || "Xe"}
        </Badge>
      </div>
      {/* Info */}
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <Camera className="h-3 w-3" /> {det.camera}
          </div>
          <span className="text-[10px] text-zinc-500 font-mono">{formatVN(det.timestamp)}</span>
        </div>
        {/* Color dots */}
        <div className="flex gap-1 flex-wrap">
          {colors.slice(0, 4).map((c, i) => (
            <span key={i} className="w-4 h-4 rounded-full border border-zinc-600" style={{ backgroundColor: `rgb(${c.rgb.join(",")})` }} title={c.name} />
          ))}
          {det.license_plate && (
            <span className="text-[10px] text-amber-400 font-mono ml-auto">{det.license_plate}</span>
          )}
        </div>
        {det.track_id != null && (
          <div className="text-[10px] text-zinc-500">Track #{det.track_id}</div>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────
export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState("all");
  const [search, setSearch] = useState("");
  const [cameraFilter, setCameraFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [detections, setDetections] = useState<DetectionDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [cameras, setCameras] = useState<{ camera_id: string; name: string }[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>("table");

  // Advanced filters
  const [showFilters, setShowFilters] = useState(false);
  const [shirtColor, setShirtColor] = useState<string | null>(null);
  const [pantsColor, setPantsColor] = useState<string | null>(null);
  const [vehicleColor, setVehicleColor] = useState<string | null>(null);
  const [vehicleType, setVehicleType] = useState<string>("all");
  const [minConfidence, setMinConfidence] = useState(0);
  const [dateFrom, setDateFrom] = useState<Date | undefined>();
  const [dateTo, setDateTo] = useState<Date | undefined>();
  const [selectedDetection, setSelectedDetection] = useState<DetectionDetail | null>(null);

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
      const results: DetectionDetail[] = [];
      let totalCount = 0;
      const camParam = cameraFilter !== "all" ? cameraFilter : undefined;
      const baseParams: Record<string, unknown> = {
        page: currentPage,
        per_page: itemsPerPage,
        camera_id: camParam,
        min_confidence: minConfidence > 0 ? minConfidence / 100 : undefined,
        date_from: dateFrom?.toISOString(),
        date_to: dateTo?.toISOString(),
      };

      if (activeTab === "all" || activeTab === "person") {
        const res = await api.get("/persons", {
          params: {
            ...baseParams,
            shirt_color: shirtColor || undefined,
            pants_color: pantsColor || undefined,
          },
        });
        const persons = (res.data.persons || []).map((p: Record<string, unknown>) => ({
          id: `p_${p.id}`,
          type: "person" as const,
          camera: String(p.camera_id || ""),
          timestamp: String(p.timestamp || ""),
          confidence: Number(p.confidence) || 0,
          track_id: p.track_id as number | undefined,
          image_path: p.image_path as string | undefined,
          full_frame_path: (p.attributes as Record<string, unknown>)?.full_frame_path as string | undefined,
          bbox: p.bbox as number[] | undefined,
          shirt_colors: p.shirt_colors as ColorInfo[] | undefined,
          pants_colors: p.pants_colors as ColorInfo[] | undefined,
          hair_colors: p.hair_colors as ColorInfo[] | undefined,
        }));
        results.push(...persons);
        totalCount += res.data.total || 0;
      }

      if (activeTab === "all" || activeTab === "vehicle") {
        const res = await api.get("/vehicles", {
          params: {
            ...baseParams,
            vehicle_type: vehicleType !== "all" ? vehicleType : undefined,
            vehicle_color: vehicleColor || undefined,
            license_plate: search || undefined,
          },
        });
        const vehicles = (res.data.vehicles || []).map((v: Record<string, unknown>) => ({
          id: `v_${v.id}`,
          type: "vehicle" as const,
          camera: String(v.camera_id || ""),
          timestamp: String(v.timestamp || ""),
          confidence: Number(v.confidence) || 0,
          track_id: v.track_id as number | undefined,
          image_path: v.image_path as string | undefined,
          full_frame_path: v.full_frame_path as string | undefined,
          bbox: v.bbox as number[] | undefined,
          vehicle_type: String(v.vehicle_type || ""),
          vehicle_colors: v.vehicle_colors as ColorInfo[] | undefined,
          license_plate: v.license_plate as string | undefined,
        }));
        results.push(...vehicles);
        totalCount += res.data.total || 0;
      }

      results.sort((a, b) => (b.timestamp > a.timestamp ? 1 : -1));
      setDetections(results);
      setTotal(totalCount);
    } catch (err) {
      console.warn("History fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, currentPage, cameraFilter, shirtColor, pantsColor, vehicleColor, vehicleType, minConfidence, dateFrom, dateTo, search]);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { setCurrentPage(1); }, [activeTab, cameraFilter, shirtColor, pantsColor, vehicleColor, vehicleType, minConfidence, dateFrom, dateTo, search]);

  const filtered = search && activeTab !== "vehicle"
    ? detections.filter((d) =>
        d.camera.toLowerCase().includes(search.toLowerCase()) ||
        (d.license_plate && d.license_plate.toLowerCase().includes(search.toLowerCase()))
      )
    : detections;

  const totalPages = Math.max(1, Math.ceil(total / itemsPerPage));
  const activeFiltersCount = [shirtColor, pantsColor, vehicleColor, vehicleType !== "all" ? vehicleType : null, minConfidence > 0 ? "conf" : null, dateFrom, dateTo].filter(Boolean).length;

  const clearFilters = () => {
    setShirtColor(null); setPantsColor(null); setVehicleColor(null);
    setVehicleType("all"); setMinConfidence(0); setDateFrom(undefined); setDateTo(undefined);
    setSearch("");
  };

  return (
    <div className="flex flex-col gap-4">
      {/* ─── Top Bar ─── */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <Input placeholder="Tìm kiếm biển số..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-500" />
        </div>
        <Select value={cameraFilter} onValueChange={(v) => setCameraFilter(v ?? "all")}>
          <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-zinc-300">
            <SelectValue placeholder="Camera" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-800">
            <SelectItem value="all">Tất cả camera</SelectItem>
            {cameras.map((c) => (
              <SelectItem key={c.camera_id} value={c.camera_id}>{c.camera_id} - {c.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Date Range */}
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" className="border-zinc-800 text-zinc-300 bg-zinc-900 hover:bg-zinc-800 gap-2">
              <CalendarIcon className="h-4 w-4" />
              {dateFrom ? format(dateFrom, "dd/MM", { locale: vi }) : "Từ"} — {dateTo ? format(dateTo, "dd/MM", { locale: vi }) : "Đến"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar mode="range" selected={{ from: dateFrom, to: dateTo }}
              onSelect={(range: { from?: Date; to?: Date } | undefined) => { setDateFrom(range?.from); setDateTo(range?.to); }}
              locale={vi} />
          </PopoverContent>
        </Popover>

        {/* Advanced filter toggle */}
        <Button variant="outline" onClick={() => setShowFilters(!showFilters)}
          className={`border-zinc-800 text-zinc-300 bg-zinc-900 hover:bg-zinc-800 gap-2 ${showFilters ? "border-blue-500 text-blue-300" : ""}`}>
          <SlidersHorizontal className="h-4 w-4" />
          Bộ lọc {activeFiltersCount > 0 && <Badge className="bg-blue-600 text-white text-[10px] ml-1">{activeFiltersCount}</Badge>}
        </Button>

        {activeFiltersCount > 0 && (
          <Button variant="ghost" onClick={clearFilters} className="text-zinc-500 hover:text-zinc-300 text-xs">
            Xóa bộ lọc
          </Button>
        )}

        {/* View toggle */}
        <div className="flex ml-auto border border-zinc-800 rounded-md overflow-hidden">
          <button onClick={() => setViewMode("table")}
            className={`p-2 ${viewMode === "table" ? "bg-zinc-700 text-white" : "bg-zinc-900 text-zinc-500 hover:text-zinc-300"}`}>
            <List className="h-4 w-4" />
          </button>
          <button onClick={() => setViewMode("grid")}
            className={`p-2 ${viewMode === "grid" ? "bg-zinc-700 text-white" : "bg-zinc-900 text-zinc-500 hover:text-zinc-300"}`}>
            <LayoutGrid className="h-4 w-4" />
          </button>
        </div>
        {loading && <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />}
      </div>

      {/* ─── Advanced Filters Panel ─── */}
      {showFilters && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-3 animate-in slide-in-from-top-2">
          {/* Shirt color */}
          {(activeTab === "all" || activeTab === "person") && (
            <div className="space-y-2">
              <span className="text-xs text-zinc-500 uppercase tracking-wide">Màu áo</span>
              <div className="flex gap-1.5 flex-wrap">
                {ALL_COLORS.map((c) => (
                  <ColorChip key={c} name={c} active={shirtColor === c} onClick={() => setShirtColor(shirtColor === c ? null : c)} />
                ))}
              </div>
            </div>
          )}
          {(activeTab === "all" || activeTab === "person") && (
            <div className="space-y-2">
              <span className="text-xs text-zinc-500 uppercase tracking-wide">Màu quần</span>
              <div className="flex gap-1.5 flex-wrap">
                {ALL_COLORS.map((c) => (
                  <ColorChip key={c} name={c} active={pantsColor === c} onClick={() => setPantsColor(pantsColor === c ? null : c)} />
                ))}
              </div>
            </div>
          )}
          {/* Vehicle filters */}
          {(activeTab === "all" || activeTab === "vehicle") && (
            <div className="flex gap-4 items-end flex-wrap">
              <div className="space-y-2">
                <span className="text-xs text-zinc-500 uppercase tracking-wide">Loại xe</span>
                <Select value={vehicleType} onValueChange={(v) => setVehicleType(v ?? "all")}>
                  <SelectTrigger className="w-[140px] bg-zinc-800 border-zinc-700 text-zinc-300 h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-800">
                    <SelectItem value="all">Tất cả</SelectItem>
                    {VEHICLE_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <span className="text-xs text-zinc-500 uppercase tracking-wide">Màu xe</span>
                <div className="flex gap-1.5 flex-wrap">
                  {ALL_COLORS.slice(0, 8).map((c) => (
                    <ColorChip key={c} name={c} active={vehicleColor === c} onClick={() => setVehicleColor(vehicleColor === c ? null : c)} />
                  ))}
                </div>
              </div>
            </div>
          )}
          {/* Confidence slider */}
          <div className="flex items-center gap-4">
            <span className="text-xs text-zinc-500 uppercase tracking-wide w-28">Độ tin cậy ≥</span>
            <Slider value={[minConfidence]} onValueChange={(v) => setMinConfidence(v[0])} max={100} step={5} className="flex-1 max-w-xs" />
            <span className="text-xs text-zinc-300 font-mono w-10">{minConfidence}%</span>
          </div>
        </div>
      )}

      {/* ─── Tabs ─── */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">Tất cả ({total})</TabsTrigger>
          <TabsTrigger value="person" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <Users className="h-4 w-4 mr-1.5" /> Người
          </TabsTrigger>
          <TabsTrigger value="vehicle" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <Car className="h-4 w-4 mr-1.5" /> Phương tiện
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* ─── Grid View ─── */}
      {viewMode === "grid" ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {filtered.length === 0 && !loading ? (
            <div className="col-span-full text-center text-zinc-500 py-12">Không có dữ liệu</div>
          ) : (
            filtered.map((det) => (
              <DetectionCard key={det.id} det={det} onClick={() => setSelectedDetection(det)} />
            ))
          )}
        </div>
      ) : (
        /* ─── Table View ─── */
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-zinc-900">
                <TableHead className="text-zinc-400 w-12">#</TableHead>
                <TableHead className="text-zinc-400 w-16">Ảnh</TableHead>
                <TableHead className="text-zinc-400">Loại</TableHead>
                <TableHead className="text-zinc-400">Camera</TableHead>
                <TableHead className="text-zinc-400">Thời gian</TableHead>
                <TableHead className="text-zinc-400">Đặc điểm</TableHead>
                <TableHead className="text-zinc-400">Độ tin cậy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 && !loading ? (
                <TableRow><TableCell colSpan={7} className="text-center text-zinc-500 py-12">Không có dữ liệu</TableCell></TableRow>
              ) : (
                filtered.map((det, idx) => {
                  const isPerson = det.type === "person";
                  const imgSrc = cropUrl(det.image_path);
                  const colors: ColorInfo[] = isPerson ? [...(det.shirt_colors || []), ...(det.pants_colors || [])] : (det.vehicle_colors || []);
                  const conf = Math.round(det.confidence * 100);
                  const attrs: string[] = [];
                  if (isPerson) {
                    det.shirt_colors?.slice(0, 2).forEach((c) => attrs.push(`Áo: ${c.name}`));
                    det.pants_colors?.slice(0, 2).forEach((c) => attrs.push(`Quần: ${c.name}`));
                  } else {
                    if (det.vehicle_type) attrs.push(det.vehicle_type);
                    if (det.license_plate) attrs.push(det.license_plate);
                  }
                  if (det.track_id != null) attrs.push(`Track #${det.track_id}`);

                  return (
                    <TableRow key={det.id} className="border-zinc-800 hover:bg-zinc-800/50 cursor-pointer"
                      onClick={() => setSelectedDetection(det)}>
                      <TableCell className="text-zinc-500 text-sm">{(currentPage - 1) * itemsPerPage + idx + 1}</TableCell>
                      <TableCell>
                        <div className="w-10 h-12 bg-zinc-800 rounded overflow-hidden">
                          {imgSrc ? (
                            <img src={imgSrc} alt="" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-zinc-600">
                              {isPerson ? <Users className="h-4 w-4" /> : <Car className="h-4 w-4" />}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={`${isPerson ? "bg-blue-500/10 text-blue-400" : "bg-emerald-500/10 text-emerald-400"} border-transparent text-[11px]`}>
                          {isPerson ? "Người" : "Xe"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-zinc-300 text-sm">
                          <Camera className="h-3.5 w-3.5 text-zinc-500" /> {det.camera}
                        </div>
                      </TableCell>
                      <TableCell className="text-zinc-400 text-sm font-mono">{det.timestamp}</TableCell>
                      <TableCell>
                        <div className="flex gap-1 items-center flex-wrap">
                          {colors.slice(0, 3).map((c, i) => (
                            <span key={i} className="w-3.5 h-3.5 rounded-full border border-zinc-600 inline-block" style={{ backgroundColor: `rgb(${c.rgb.join(",")})` }} title={c.name} />
                          ))}
                          {attrs.map((a) => (
                            <Badge key={a} variant="secondary" className="bg-zinc-800 text-zinc-300 border-zinc-700 text-[11px]">{a}</Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${conf >= 80 ? "bg-emerald-500" : conf >= 60 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${conf}%` }} />
                          </div>
                          <span className="text-[11px] text-zinc-400 font-mono">{conf}%</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {/* ─── Pagination ─── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-500">Trang {currentPage} / {totalPages} — {total} kết quả</span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" disabled={currentPage === 1} onClick={() => setCurrentPage((p) => p - 1)}
              className="border-zinc-800 text-zinc-400 hover:text-white disabled:opacity-30"><ChevronLeft className="h-4 w-4" /></Button>
            <Button variant="outline" size="icon" disabled={currentPage >= totalPages} onClick={() => setCurrentPage((p) => p + 1)}
              className="border-zinc-800 text-zinc-400 hover:text-white disabled:opacity-30"><ChevronRight className="h-4 w-4" /></Button>
          </div>
        </div>
      )}

      {/* ─── Detail Modal ─── */}
      <DetectionModal detection={selectedDetection} open={!!selectedDetection} onClose={() => setSelectedDetection(null)} />
    </div>
  );
}
