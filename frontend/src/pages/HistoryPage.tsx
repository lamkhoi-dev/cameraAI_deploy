import { useState } from "react";
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
  AlertTriangle,
  Camera,
  Eye,
} from "lucide-react";

interface Detection {
  id: string;
  type: "person" | "vehicle" | "alert";
  camera: string;
  timestamp: string;
  attributes: string[];
  confidence: number;
  thumbnail?: string;
}

const demoDetections: Detection[] = [
  { id: "1", type: "person", camera: "Cam 01 - Sảnh A", timestamp: "05/05/2026 14:30:22", attributes: ["Nam", "Áo trắng"], confidence: 92 },
  { id: "2", type: "vehicle", camera: "Cam 02 - Bãi xe B1", timestamp: "05/05/2026 14:28:15", attributes: ["Ô tô", "51A-12345"], confidence: 88 },
  { id: "3", type: "person", camera: "Cam 05 - Cổng chính", timestamp: "05/05/2026 14:25:03", attributes: ["Nữ", "Áo đen"], confidence: 85 },
  { id: "4", type: "alert", camera: "Cam 04 - Kho Hàng", timestamp: "05/05/2026 14:20:11", attributes: ["Khói"], confidence: 95 },
  { id: "5", type: "vehicle", camera: "Cam 02 - Bãi xe B1", timestamp: "05/05/2026 14:15:47", attributes: ["Xe máy", "59P1-67890"], confidence: 72 },
  { id: "6", type: "person", camera: "Cam 08 - Thang máy A", timestamp: "05/05/2026 14:10:33", attributes: ["Nam", "Mũ bảo hiểm"], confidence: 79 },
  { id: "7", type: "person", camera: "Cam 01 - Sảnh A", timestamp: "05/05/2026 14:05:19", attributes: ["Nam", "Vest"], confidence: 91 },
  { id: "8", type: "vehicle", camera: "Cam 05 - Cổng chính", timestamp: "05/05/2026 13:58:42", attributes: ["Ô tô", "30A-98765"], confidence: 94 },
];

const typeConfig = {
  person: { icon: Users, color: "text-blue-400", bg: "bg-blue-500/10", label: "Người" },
  vehicle: { icon: Car, color: "text-emerald-400", bg: "bg-emerald-500/10", label: "Phương tiện" },
  alert: { icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10", label: "Cảnh báo" },
};

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState("all");
  const [search, setSearch] = useState("");
  const [cameraFilter, setCameraFilter] = useState<string | null>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const filtered = demoDetections.filter((d) => {
    const matchTab = activeTab === "all" || d.type === activeTab;
    const matchSearch =
      search === "" ||
      d.camera.toLowerCase().includes(search.toLowerCase()) ||
      d.attributes.some((a) => a.toLowerCase().includes(search.toLowerCase()));
    const matchCamera = !cameraFilter || cameraFilter === "all" || d.camera.includes(cameraFilter);
    return matchTab && matchSearch && matchCamera;
  });

  const totalPages = Math.ceil(filtered.length / itemsPerPage);
  const paginatedData = filtered.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

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
          <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-zinc-300">
            <SelectValue placeholder="Camera" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-800">
            <SelectItem value="all">Tất cả camera</SelectItem>
            <SelectItem value="Cam 01">Cam 01 - Sảnh A</SelectItem>
            <SelectItem value="Cam 02">Cam 02 - Bãi xe B1</SelectItem>
            <SelectItem value="Cam 04">Cam 04 - Kho Hàng</SelectItem>
            <SelectItem value="Cam 05">Cam 05 - Cổng chính</SelectItem>
            <SelectItem value="Cam 08">Cam 08 - Thang máy A</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Tất cả
          </TabsTrigger>
          <TabsTrigger value="person" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <Users className="h-4 w-4 mr-1.5" />
            Người
          </TabsTrigger>
          <TabsTrigger value="vehicle" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <Car className="h-4 w-4 mr-1.5" />
            Phương tiện
          </TabsTrigger>
          <TabsTrigger value="alert" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            <AlertTriangle className="h-4 w-4 mr-1.5" />
            Cảnh báo
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
              <TableHead className="text-zinc-400 text-right">Chi tiết</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedData.map((det, idx) => {
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
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-white">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-500">
            Hiển thị {(currentPage - 1) * itemsPerPage + 1}-
            {Math.min(currentPage * itemsPerPage, filtered.length)} / {filtered.length} kết quả
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
            {Array.from({ length: totalPages }, (_, i) => (
              <Button
                key={i}
                variant={currentPage === i + 1 ? "default" : "outline"}
                size="icon"
                onClick={() => setCurrentPage(i + 1)}
                className={
                  currentPage === i + 1
                    ? "bg-blue-600 text-white"
                    : "border-zinc-800 text-zinc-400 hover:text-white"
                }
              >
                {i + 1}
              </Button>
            ))}
            <Button
              variant="outline"
              size="icon"
              disabled={currentPage === totalPages}
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
