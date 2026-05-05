import { useEffect, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";
// Socket.IO connects to the root, not /api
const SOCKET_URL = API_BASE.replace("/api", "");

type SocketEventHandler = (data: unknown) => void;

interface UseSocketOptions {
  rooms?: string[];
  events?: Record<string, SocketEventHandler>;
  enabled?: boolean;
}

/**
 * Hook to connect to Flask-SocketIO backend.
 * Supports subscribing to rooms and listening to events.
 */
export function useSocket({ rooms = [], events = {}, enabled = true }: UseSocketOptions = {}) {
  const socketRef = useRef<Socket | null>(null);
  const eventsRef = useRef(events);
  eventsRef.current = events;

  useEffect(() => {
    if (!enabled) return;

    const socket = io(SOCKET_URL, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: Infinity,
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      console.log("[SocketIO] Connected:", socket.id);

      // Subscribe to rooms
      rooms.forEach((room) => {
        socket.emit(`subscribe_${room}`);
      });
    });

    socket.on("disconnect", (reason) => {
      console.log("[SocketIO] Disconnected:", reason);
    });

    socket.on("connect_error", (error) => {
      console.warn("[SocketIO] Connection error:", error.message);
    });

    // Register event listeners
    const currentEvents = eventsRef.current;
    Object.entries(currentEvents).forEach(([event, handler]) => {
      socket.on(event, handler);
    });

    return () => {
      Object.entries(currentEvents).forEach(([event, handler]) => {
        socket.off(event, handler);
      });
      socket.disconnect();
      socketRef.current = null;
    };
  }, [enabled, rooms.join(",")]); // eslint-disable-line react-hooks/exhaustive-deps

  const emit = useCallback((event: string, data?: unknown) => {
    socketRef.current?.emit(event, data);
  }, []);

  return { socket: socketRef.current, emit };
}
