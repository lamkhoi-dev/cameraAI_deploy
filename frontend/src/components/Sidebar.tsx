import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  MonitorPlay,
  Camera,
  ShieldAlert,
  History,
  Settings,
  LogOut,
  Video,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Tổng quan" },
  { to: "/live", icon: MonitorPlay, label: "Camera Live" },
  { to: "/cameras", icon: Camera, label: "Quản lý Camera" },
  { to: "/alerts", icon: ShieldAlert, label: "Cảnh báo", badge: true },
  { to: "/history", icon: History, label: "Lịch sử" },
  { to: "/settings", icon: Settings, label: "Cài đặt" },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <nav className="fixed left-0 top-0 h-full w-[240px] border-r border-zinc-800 bg-[#09090b] flex flex-col gap-1 p-4 z-50">
      {/* Brand */}
      <div className="flex items-center gap-3 px-2 py-4 mb-6">
        <Video className="h-7 w-7 text-blue-500" />
        <div className="flex flex-col">
          <span className="text-[15px] font-bold text-zinc-100 uppercase tracking-widest">
            CamCore AI
          </span>
          <span className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider">
            v2.0
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive =
            item.to === "/"
              ? location.pathname === "/"
              : location.pathname.startsWith(item.to);

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={cn(
                "flex items-center justify-between px-3 py-2 text-sm transition-all duration-150 active:scale-[0.98]",
                isActive
                  ? "bg-zinc-800 text-white border-l-2 border-blue-500 font-semibold"
                  : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 border-l-2 border-transparent"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="bg-red-500/20 text-red-400 text-[11px] font-medium px-2 py-0.5 rounded-full border border-red-500/30">
                  3
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* User Profile */}
      <div className="mt-auto pt-4 border-t border-zinc-800">
        <div className="flex items-center justify-between px-2 py-2 hover:bg-zinc-900 rounded-lg cursor-pointer transition-colors">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-zinc-800 border border-zinc-700 rounded-lg flex items-center justify-center">
              <span className="text-zinc-400 text-xs font-bold">
                {user?.username?.charAt(0).toUpperCase() || "A"}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium text-zinc-200">
                {user?.username || "admin"}
              </span>
              <span className="text-[12px] text-zinc-500">Quản trị viên</span>
            </div>
          </div>
          <button
            onClick={logout}
            className="text-zinc-500 hover:text-red-400 transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
