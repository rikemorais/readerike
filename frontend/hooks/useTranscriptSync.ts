"use client";

import { useEffect, useRef, useState } from "react";
import type { Segment } from "@/types";

export function useTranscriptSync(segments: Segment[]) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onTimeUpdate = () => {
      const t = video.currentTime;
      const idx = segments.findIndex((s) => t >= s.start && t < s.end);
      setActiveIndex(idx);
    };

    video.addEventListener("timeupdate", onTimeUpdate);
    return () => video.removeEventListener("timeupdate", onTimeUpdate);
  }, [segments]);

  const seekTo = (start: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = start;
      videoRef.current.play();
    }
  };

  return { videoRef, activeIndex, seekTo };
}
