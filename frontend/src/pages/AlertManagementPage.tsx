import { useState, useEffect, useCallback } from "react";
import api from "@/api/client";
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
  Loader2,
  RefreshCw,
} from "lucide-react";

type AlertStatus = "active" | "resolved";

interface Alert {
  id: number;
  alert_type: string;
  camera_id: string;
  severity: string;
  status: AlertStatus;
  confidence: number;
  description: string | null;
  location: string | null;
  timestamp: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
}

const typeConfig: Record<string, { icon: typeof Flame; color: string; bg: string; border: string }> = {
  fire: { icon: Flame, color: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/30" },
  smoke: { icon: Flame, color: "text-orange-500", bg: "bg-orange-500/10", border: "border-orange-500/30" },
  intrusion: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30" },
  suspicious: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30" },
  person: { icon: Users, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/30" },
  vehicle: { icon: Car, color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
  info: { icon: AlertTriangle, color: "text-zinc-400", bg: "bg-zinc-800", border: "border-zinc-700" },
};

function getTypeConfig(alertType: string) {
  return typeConfig[alertType] || typeConfig.info;
}

function formatTime(ts: string | null) {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

function formatDate(ts: string | null) {
  if (!ts) return "";
  return new Date(ts).toLocaleDateString("vi-VN");
}

export default function AlertManagementPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeTab, setActiveTab] = useState("all");
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { per_page: "50" };
      if (activeTab === "active" || activeTab === "resolved") {
        params.status = activeTab;
      } else if (activeTab !== "all") {
        params.alert_type = activeTab;
      }
      const res = await api.get("/alerts", { params });
      const list = res.data.alerts || [];
      setAlerts(list);
      setTotal(res.data.total || 0);
      if (list.length > 0 && !selectedAlert) {
        setSelectedAlert(list[0]);
      }
    } catch (err) {
      console.warn("Alerts fetch failed:", err);
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const filteredAlerts = alerts;
  const pendingCount = alerts.filter((a) => a.status === "active").length;

  const markResolved = async (id: number) => {
    try {
      await api.put(`/alerts/${id}/resolve`);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: "resolved" as AlertStatus } : a))
      );
      if (selectedAlert?.id === id) {
        setSelectedAlert((s) => (s ? { ...s, status: "resolved" } : s));
      }
    } catch (err) {
      console.warn("Resolve alert failed:", err);
    }
  };

  return (
    <div className="flex flex-col gap-6 h-[calc(100vh-7rem)]">
      {/* Filter Tabs */}
      <div className="flex items-center gap-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-zinc-900 border border-zinc-800">
            <TabsTrigger value="all" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
              Tất cả ({total})
            </TabsTrigger>
            <TabsTrigger value="active" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400">
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
        <Button variant="ghost" size="icon" onClick={fetchAlerts} className="text-zinc-400 hover:text-white">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        </Button>
      </div>

      {/* Split View */}
      <div className="flex gap-6 flex-1 overflow-hidden">
        {/* Alert List (60%) */}
        <ScrollArea className="flex-1 min-w-0">
          <div className="flex flex-col gap-2 pr-4">
            {filteredAlerts.length === 0 && !loading ? (
              <div className="text-center text-zinc-500 py-12">
                Không có cảnh báo nào
              </div>
            ) : (
              filteredAlerts.map((alert) => {
                const config = getTypeConfig(alert.alert_type);
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
                        <span className={cn("text-sm font-medium", config.color)}>
                          {alert.alert_type} — {alert.camera_id}
                        </span>
                        <span className="text-[11px] text-zinc-500">{formatTime(alert.timestamp)}</span>
                      </div>
                      <span className="text-[12px] text-zinc-400 block mt-0.5">
                        {alert.description || alert.location || alert.camera_id}
                      </span>
                      <div className="flex items-center gap-2 mt-2">
                        {alert.status === "active" ? (
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
                        <span className="text-[10px] text-zinc-500">Conf: {Math.round(alert.confidence * 100)}%</span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
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
                <h3 className="text-lg font-semibold text-white">
                  {selectedAlert.alert_type} — {selectedAlert.camera_id}
                </h3>
                <p className="text-sm text-zinc-400 mt-1">
                  {selectedAlert.description || "Không có mô tả"}
                </p>
              </div>

              <Separator className="bg-zinc-800" />

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Camera className="h-4 w-4" />
                  <span>{selectedAlert.camera_id}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <MapPin className="h-4 w-4" />
                  <span>{selectedAlert.location || selectedAlert.camera_id}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <Clock className="h-4 w-4" />
                  <span>{formatTime(selectedAlert.timestamp)} — {formatDate(selectedAlert.timestamp)}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Conf: {Math.round(selectedAlert.confidence * 100)}%</span>
                </div>
              </div>

              <Separator className="bg-zinc-800" />

              {/* Actions */}
              {selectedAlert.status === "active" && (
                <Button
                  onClick={() => markResolved(selectedAlert.id)}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white w-full"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Đánh dấu đã xử lý
                </Button>
              )}
              {selectedAlert.status === "resolved" && selectedAlert.resolved_by && (
                <div className="text-sm text-zinc-500">
                  Xử lý bởi: <span className="text-zinc-300">{selectedAlert.resolved_by}</span>
                  {selectedAlert.resolved_at && (
                    <span> lúc {formatTime(selectedAlert.resolved_at)} {formatDate(selectedAlert.resolved_at)}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
