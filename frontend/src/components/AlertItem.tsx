import { cn } from "@/lib/utils";
import { Flame, AlertTriangle, Info } from "lucide-react";

interface AlertItemData {
  id: string;
  type: "fire" | "intrusion" | "info";
  title: string;
  source: string;
  time: string;
}

const alertConfig = {
  fire: {
    icon: Flame,
    iconColor: "text-red-500",
    bgColor: "bg-red-500/20",
    borderColor: "border-red-500/30",
    titleColor: "text-red-400",
    cardBorder: "border-red-900/30",
    cardBg: "bg-red-950/10",
  },
  intrusion: {
    icon: AlertTriangle,
    iconColor: "text-amber-500",
    bgColor: "bg-amber-500/20",
    borderColor: "border-amber-500/30",
    titleColor: "text-amber-400",
    cardBorder: "border-amber-900/30",
    cardBg: "bg-amber-950/10",
  },
  info: {
    icon: Info,
    iconColor: "text-zinc-400",
    bgColor: "bg-zinc-800",
    borderColor: "border-zinc-700",
    titleColor: "text-zinc-300",
    cardBorder: "border-zinc-800",
    cardBg: "",
  },
};

export function AlertItem({ alert }: { alert: AlertItemData }) {
  const config = alertConfig[alert.type];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "p-3 border rounded-lg flex gap-3 items-start hover:bg-zinc-800 transition-colors cursor-pointer",
        config.cardBorder,
        config.cardBg
      )}
    >
      <div
        className={cn(
          "mt-0.5 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 border",
          config.bgColor,
          config.borderColor
        )}
      >
        <Icon className={cn("h-3.5 w-3.5", config.iconColor)} />
      </div>
      <div className="flex flex-col gap-1 w-full">
        <div className="flex justify-between items-start">
          <span className={cn("text-sm font-medium", config.titleColor)}>
            {alert.title}
          </span>
          <span className="text-[11px] font-medium text-zinc-500">
            {alert.time}
          </span>
        </div>
        <span className="text-[12px] text-zinc-400">{alert.source}</span>
      </div>
    </div>
  );
}

export type { AlertItemData };
