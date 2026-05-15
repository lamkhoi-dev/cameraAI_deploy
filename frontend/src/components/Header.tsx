import { useLocation } from "react-router-dom";
import { Bell } from "lucide-react";
import { useEffect, useState } from "react";

const pageTitles: Record<string, string> = {
  "/": "Tổng quan hệ thống",
  "/live": "Camera Live View",
  "/cameras": "Quản lý Camera",
  "/alerts": "Quản lý cảnh báo",
  "/history": "Lịch sử phát hiện",
  "/settings": "Cài đặt hệ thống",
};

export function Header() {
  const location = useLocation();
  const [clock, setClock] = useState("");

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const time = now.toLocaleTimeString("vi-VN", { hour12: false });
      const date = now.toLocaleDateString("vi-VN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
      setClock(`${time} | ${date}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const title = pageTitles[location.pathname] || "CamCore AI";

  return (
    <header className="fixed top-0 right-0 w-[calc(100%-240px)] h-16 border-b border-zinc-800 bg-[#09090b]/80 backdrop-blur-md flex items-center justify-between px-6 z-40">
      <div className="flex items-center gap-4">
        <h1 className="font-bold text-[18px] text-white tracking-tight">
          {title}
        </h1>
      </div>

      <div className="flex items-center gap-6">
        {/* Online Status */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-medium tracking-wider uppercase text-zinc-300">
            Trực tuyến
          </span>
        </div>

        <div className="h-4 w-px bg-zinc-800" />

        {/* Clock */}
        <span className="text-[11px] font-medium tracking-wider text-zinc-400">
          {clock}
        </span>

        <div className="h-4 w-px bg-zinc-800" />

        {/* Notification Bell */}
        <button className="text-zinc-400 hover:text-white transition-colors relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full border border-zinc-900" />
        </button>
      </div>
    </header>
  );
}
