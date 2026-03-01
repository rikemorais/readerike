"use client";

import { useEffect, useRef } from "react";
import { downloadUrl, videoUrl } from "@/lib/api";
import { useTranscriptSync } from "@/hooks/useTranscriptSync";
import type { Job } from "@/types";

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export function TranscriptViewer({ job }: { job: Job }) {
  const segments = job.transcription?.segments ?? [];
  const { videoRef, activeIndex, seekTo } = useTranscriptSync(segments);
  const activeSegRef = useRef<HTMLButtonElement | null>(null);

  // Auto-scroll to active segment
  useEffect(() => {
    activeSegRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [activeIndex]);

  const ext = job.video_filename.substring(job.video_filename.lastIndexOf("."));

  return (
    <div className="flex h-full flex-col gap-6 lg:flex-row">
      <div className="lg:w-1/2">
        <video
          ref={videoRef}
          src={videoUrl(`${job.id}${ext}`)}
          controls
          className="w-full rounded-xl bg-black"
        />
        <div className="mt-4 flex gap-2">
          {(["json", "txt", "srt"] as const).map((fmt) => (
            <a
              key={fmt}
              href={downloadUrl(job.id, fmt)}
              download
              className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              Export {fmt.toUpperCase()}
            </a>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-xl border border-gray-200 bg-white p-4 lg:h-[70vh]">
        <p className="mb-3 text-xs text-gray-500">
          {job.transcription?.language && <>Language: {job.transcription.language} · </>}
          {segments.length} segments
        </p>
        <div className="space-y-1">
          {segments.map((seg, idx) => (
            <button
              key={idx}
              ref={idx === activeIndex ? activeSegRef : null}
              onClick={() => seekTo(seg.start)}
              className={`block w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                idx === activeIndex
                  ? "bg-indigo-50 font-medium text-indigo-900"
                  : "text-gray-700 hover:bg-gray-50"
              }`}
            >
              <span className="mr-2 text-xs text-gray-400">{formatTime(seg.start)}</span>
              {seg.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
