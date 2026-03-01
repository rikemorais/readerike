"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { wsUrl } from "@/lib/api";
import type { Job, WsEvent } from "@/types";

export type WsState = {
  step: string | null;
  pct: number;
  completed: Job | null;
  error: string | null;
};

export function useJobWebSocket(
  jobId: string | null,
  active = true
): WsState {
  const [state, setState] = useState<WsState>({
    step: null,
    pct: 0,
    completed: null,
    error: null,
  });
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!jobId || !active) return;
    const ws = new WebSocket(wsUrl(jobId));
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data as string) as WsEvent;
      if (data.event === "progress") {
        setState((s) => ({ ...s, step: data.step, pct: data.pct }));
      } else if (data.event === "completed") {
        setState((s) => ({ ...s, completed: data.job, pct: 100 }));
        ws.close();
      } else if (data.event === "error") {
        setState((s) => ({ ...s, error: data.message }));
        ws.close();
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  }, [jobId, active]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return state;
}
