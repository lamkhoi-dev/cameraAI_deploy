
import { VideoOff, Users, Car } from "lucide-react";
import { useEffect, useState } from "react";

interface CameraTileProps {
  name: string;
  status: "online" | "offline";
  streamUrl?: string;
  resolution?: string;
  protocol?: string;
  aiTags?: string[];
  events?: { persons: number; vehicles: number };
}

export function CameraTile({
  name,
  status,
  streamUrl,
  resolution = "1080P / 30FPS",
  protocol = "RTC",
  aiTags = [],
  events,
}: CameraTileProps) {
  const isOnline = status === "online";
  const [showEvent, setShowEvent] = useState(false);
  const [eventData, setEventData] = useState({ persons: 0, vehicles: 0 });

  useEffect(() => {
    if (!events || (events.persons === 0 && events.vehicles === 0)) return;
    setEventData(events);
    setShowEvent(true);
    const timer = setTimeout(() => setShowEvent(false), 4000);
    return () => clearTimeout(timer);
  }, [events]);

  return (
    <div className="relative bg-black rounded-lg overflow-hidden aspect-video group">
      {isOnline && streamUrl ? (
        <>
          {/* Video stream — fills entire tile */}
          <iframe
            src={streamUrl}
            className="absolute inset-0 w-full h-full border-0"
            allow="autoplay; fullscreen"
            title={name}
          />

          {/* Scanline overlay */}
          <div
            className="absolute inset-0 z-10 pointer-events-none"
            style={{
              background:
                "linear-gradient(to bottom, transparent, transparent 50%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.1))",
              backgroundSize: "100% 4px",
            }}
          />

          {/* Gradient overlays for text readability */}
          <div className="absolute inset-x-0 top-0 h-12 bg-gradient-to-b from-black/70 to-transparent z-20 pointer-events-none" />
          <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-black/70 to-transparent z-20 pointer-events-none" />

          {/* Top-left: Status + Name */}
          <div className="absolute top-2 left-2.5 z-30 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-semibold text-white drop-shadow-md tracking-wide">{name}</span>
          </div>

          {/* Top-right: LIVE badge */}
          <div className="absolute top-2 right-2.5 z-30">
            <span className="bg-red-600/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-sm tracking-wider animate-pulse">
              LIVE
            </span>
          </div>

          {/* Bottom-left: Resolution */}
          <div className="absolute bottom-2 left-2.5 z-30">
            <span className="text-[10px] font-medium text-zinc-300/90 drop-shadow-md">{resolution}</span>
          </div>

          {/* Bottom-right: Protocol */}
          <div className="absolute bottom-2 right-2.5 z-30">
            <span className="text-[10px] font-medium text-zinc-400/80 drop-shadow-md">{protocol}</span>
          </div>

          {/* AI Active badge */}
          {aiTags.length > 0 && (
            <div className="absolute top-2 left-1/2 -translate-x-1/2 z-30">
              <span className="text-[9px] font-medium text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.5 rounded-sm">
                AI
              </span>
            </div>
          )}

          {/* Event Realtime — animated badge */}
          {showEvent && (eventData.persons > 0 || eventData.vehicles > 0) && (
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div className="flex items-center gap-2 bg-black/70 backdrop-blur-sm border border-zinc-700/50 rounded-full px-3 py-1">
                {eventData.persons > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-blue-400 font-medium">
                    <Users className="h-3 w-3" /> {eventData.persons}
                  </span>
                )}
                {eventData.vehicles > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                    <Car className="h-3 w-3" /> {eventData.vehicles}
                  </span>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        /* Offline state */
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-zinc-950">
          <VideoOff className="h-7 w-7 text-zinc-700" />
          <span className="text-[11px] font-medium text-zinc-600 tracking-wider">
            {name}
          </span>
          <span className="text-[10px] text-zinc-700">OFFLINE</span>
        </div>
      )}
    </div>
  );
}
