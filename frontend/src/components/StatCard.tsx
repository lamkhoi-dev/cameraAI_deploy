import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  iconColor?: string;
  trend?: { value: string; up: boolean };
  subtitle?: string;
  subtitleBadge?: boolean;
  subtitleColor?: string;
}

export function StatCard({
  label,
  value,
  icon,
  trend,
  subtitle,
  subtitleBadge,
  subtitleColor,
}: StatCardProps) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 flex flex-col gap-2">
      <div className="flex justify-between items-start">
        <span className="text-sm text-zinc-400">{label}</span>
        {icon}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-white tracking-tight">
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              "text-[12px] flex items-center",
              trend.up ? "text-emerald-400" : "text-red-400"
            )}
          >
            {trend.up ? "↑" : "↓"}
            {trend.value}
          </span>
        )}
      </div>
      {subtitle && (
        <span
          className={cn(
            "text-[12px]",
            subtitleBadge
              ? `${subtitleColor || "text-amber-500 bg-amber-500/10"} px-2 py-0.5 rounded-sm w-fit`
              : "text-zinc-500"
          )}
        >
          {subtitle}
        </span>
      )}
    </div>
  );
}
