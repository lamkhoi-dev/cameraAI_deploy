import { useState } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  Flame,
  AlertTriangle,
  Users,
  Car,
  CheckCircle,
  Clock,
  MapPin,
  Camera,
} from "lucide-react";

type AlertType = "fire" | "intrusion" | "person" | "vehicle" | "info";
type AlertStatus = "pending" | "resolved";

interface Alert {
  id: string;
  type: AlertType;
  title: string;
  source: string;
  camera: string;
  time: string;
  date: string;
  status: AlertStatus;
  confidence: number;
  description: string;
  snapshot?: string;
}

const demoAlerts: Alert[] = [
  {
    id: "1",
    type: "fire",
    title: "Phát hiện khói/lửa",
    source: "Kho Hàng / Tầng 2",
    camera: "Cam 04",
    time: "14:30",
    date: "05/05/2026",
    status: "pending",
    confidence: 92,
    description: "Hệ thống AI phát hiện khói bất thường tại khu vực kho hàng tầng 2. Cảnh báo mức nghiêm trọng.",
  },
  {
    id: "2",
    type: "intrusion",
    title: "Xâm nhập khu vực hạn chế",
    source: "Sảnh A / Tầng 1",
    camera: "Cam 01",
    time: "14:15",
    date: "05/05/2026",
    status: "pending",
    confidence: 87,
    description: "Phát hiện người di chuyển vào khu vực hạn chế ngoài giờ làm việc.",
  },
  {
    id: "3",
    type: "person",
    title: "Phát hiện người lạ",
    source: "Cổng chính",
    camera: "Cam 05",
    time: "13:45",
    date: "05/05/2026",
    status: "resolved",
    confidence: 78,
    description: "Nhận diện khuôn mặt không có trong hệ thống tại khu vực cổng chính.",
  },
  {
    id: "4",
    type: "vehicle",
    title: "Xe lạ tại bãi đỗ",
    source: "Bãi xe B1",
    camera: "Cam 02",
    time: "11:20",
    date: "05/05/2026",
    status: "resolved",
    confidence: 65,
    description: "Biển số xe không nằm trong danh sách đã đăng ký.",
  },
];

const typeConfig: Record<AlertType, { icon: typeof Flame; color: string; bg: string; border: string }> = {
  fire: { icon: Flame, color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
  intrusion: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30" },
  person: { icon: Users, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/30" },
  vehicle: { icon: Car, color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
  info: { icon: AlertTriangle, color: "text-zinc-400", bg: "bg-zinc-800", border: "border-zinc-700" },
};

export default function AlertManagementPage() {
  const [alerts, setAlerts] = useState<Alert[]>(demoAlerts);
  const [activeTab, setActiveTab] = useState("all");
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(demoAlerts[0]);

  const filteredAlerts = alerts.filter((a) => {
    if (activeTab === "all") return true;
    if (activeTab === "pending") return a.status === "pending";
    if (activeTab === "resolved") return a.status === "resolved";
    return a.type === activeTab;
  });

  const pendingCount = alerts.filter((a) => a.status === "pending").length;

  const markResolved = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "resolved" as AlertStatus } : a))
    );
    if (selectedAlert?.id === id) {
      setSelectedAlert((s) => (s ? { ...s, status: "resolved" } : s));
    }
  };

  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-7rem)]">
      {/* Filter Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900 border border-zinc-800">
          <TabsTrigger value="all" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Tất cả
          </TabsTrigger>
          <TabsTrigger value="pending" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Chưa xử lý
            {pendingCount > 0 && (
              <Badge className="ml-1.5 bg-red-500/20 text-red-400 border-red-500/30 text-[10px] px-1.5">
                {pendingCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="resolved" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Đã xử lý
          </TabsTrigger>
          <TabsTrigger value="fire" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Hỏa hoạn
          </TabsTrigger>
          <TabsTrigger value="person" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Người
          </TabsTrigger>
          <TabsTrigger value="vehicle" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
            Xe
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Split View */}
      <div className="flex gap-6 flex-1 overflow-hidden">
        {/* Alert List (60%) */}
        <ScrollArea className="flex-1 min-w-0">
          <div className="flex flex-col gap-2 pr-4">
            {filteredAlerts.map((alert) => {
              const config = typeConfig[alert.type];
              const Icon = config.icon;
              return (
                <button
                  key={alert.id}
                  onClick={() => setSelectedAlert(alert)}
                  className={cn(
                    "p-4 rounded-lg border text-left transition-all w-full flex gap-3 items-start",
                    selectedAlert?.id === alert.id
                      ? "bg-zinc-800 border-blue-500/50"
                      : `bg-zinc-900 border-zinc-800 hover:bg-zinc-800/50`,
                    config.border
                  )}
                >
                  <div className={cn("mt-0.5 w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border", config.bg, config.border)}>
                    <Icon className={cn("h-4 w-4", config.color)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={cn("text-sm font-medium", config.color)}>{alert.title}</span>
                      <span className="text-[11px] text-zinc-500">{alert.time}</span>
                    </div>
                    <span className="text-[12px] text-zinc-400 block mt-0.5">{alert.source}</span>
                    <div className="flex items-center gap-2 mt-2">
                      {alert.status === "pending" ? (
                        <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-[10px]">
                          <Clock className="h-3 w-3 mr-1" />
                          Chưa xử lý
                        </Badge>
                      ) : (
                        <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 text-[10px]">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Đã xử lý
                        </Badge>
                      )}
                      <span className="text-[10px] text-zinc-500">Conf: {alert.confidence}%</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </ScrollArea>

        {/* Detail Panel (40%) */}
        {selectedAlert && (
          <div className="w-[400px] bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col overflow-hidden flex-shrink-0">
            {/* Snapshot */}
            <div className="h-48 bg-black flex items-center justify-center border-b border-zinc-800">
              <div className="text-zinc-600 flex flex-col items-center gap-2">
                <Camera className="h-8 w-8" />
                <span className="text-[11px] font-medium">Snapshot</span>
              </div>
            </div>

            {/* Metadata */}
            <div className="p-4 flex flex-col gap-4 flex-1 overflow-y-auto">
              <div>
                <h3 className="text-lg font-semibold text-white">{selectedAlert.title}</h3>
                <p className="text-sm text-zinc-400 mt-1">{selectedAlert.description}</p>
              </div>

              <Separator className="bg-zinc-800" />

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Camera className="h-4 w-4" />
                  <span>{selectedAlert.camera}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <MapPin className="h-4 w-4" />
                  <span>{selectedAlert.source}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <Clock className="h-4 w-4" />
                  <span>{selectedAlert.time} — {selectedAlert.date}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Conf: {selectedAlert.confidence}%</span>
                </div>
              </div>

              <Separator className="bg-zinc-800" />

              {/* Actions */}
              {selectedAlert.status === "pending" && (
                <Button
                  onClick={() => markResolved(selectedAlert.id)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white w-full"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Đánh dấu đã xử lý
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
