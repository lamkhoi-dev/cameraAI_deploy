import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";

export function DashboardLayout() {
  return (
    <div className="min-h-screen flex relative overflow-hidden bg-[#09090b] text-zinc-100 font-sans antialiased tracking-tight">
      {/* Grid Pattern Background */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #27272a 1px, transparent 1px), linear-gradient(to bottom, #27272a 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <Sidebar />
      <Header />

      {/* Main Content Area */}
      <main className="ml-[240px] mt-16 flex-1 relative z-10 h-[calc(100vh-4rem)] overflow-y-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
