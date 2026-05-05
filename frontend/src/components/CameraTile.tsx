import { cn } from "@/lib/utils";
import { VideoOff } from "lucide-react";

interface CameraTileProps {
  name: string;
  status: "online" | "offline";
  streamUrl?: string;
  resolution?: string;
  aiTags?: string[];
}

export function CameraTile({
  name,
  status,
  streamUrl,
  resolution = "1080P / 30FPS",
  aiTags = [],
}: CameraTileProps) {
  const isOnline = status === "online";

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg flex flex-col relative group overflow-hidden">
      {/* Top Bar */}
      <div className="px-3 py-2 flex items-center justify-between border-b border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "w-2 h-2 rounded-full",
              isOnline ? "bg-emerald-500" : "bg-zinc-600"
            )}
          />
          <span
            className={cn(
              "text-[11px] font-medium tracking-wider",
              isOnline ? "text-zinc-200" : "text-zinc-500"
            )}
          >
            {name}
          </span>
        </div>
        {isOnline ? (
          <span className="bg-red-500/20 border border-red-500/50 text-red-500 text-[11px] font-medium px-1.5 py-0.5 rounded-sm animate-pulse">
            LIVE
          </span>
        ) : (
          <span className="text-zinc-600 text-[11px] font-medium px-1.5 py-0.5">
            OFFLINE
          </span>
        )}
      </div>

      {/* Stream Area */}
      <div className="flex-1 relative bg-black flex items-center justify-center min-h-[180px]">
        {isOnline && streamUrl ? (
          <>
            {/* Scanline overlay */}
            <div
              className="absolute inset-0 z-10 pointer-events-none"
              style={{
                background:
                  "linear-gradient(to bottom, transparent, transparent 50%, rgba(0,0,0,0.15) 50%, rgba(0,0,0,0.15))",
                backgroundSize: "100% 4px",
              }}
            />
            <iframe
              src={streamUrl}
              className="w-full h-full absolute inset-0 border-0"
              allow="autoplay; fullscreen"
              title={name}
            />
            {/* Resolution badge */}
            <div className="absolute top-2 left-2 z-20">
              <span className="text-[11px] font-medium text-zinc-400 bg-black/60 px-1 py-0.5 rounded-sm">
                {resolution}
              </span>
            </div>
            {/* AI Tags */}
            {aiTags.length > 0 && (
              <div className="absolute bottom-2 right-2 z-20 flex gap-2">
                {aiTags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[11px] font-medium text-zinc-300 bg-black/60 px-2 py-1 border border-zinc-700 rounded-sm flex items-center gap-1"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 text-zinc-600">
            <VideoOff className="h-8 w-8" />
            <span className="text-[11px] font-medium tracking-wider">
              {isOnline ? "NO SIGNAL" : "OFFLINE"}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
