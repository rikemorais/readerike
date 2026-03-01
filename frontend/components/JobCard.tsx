"use client";

import Link from "next/link";
import { useJobWebSocket } from "@/hooks/useJobWebSocket";
import { ProgressBadge } from "@/components/ProgressBadge";
import type { JobListItem } from "@/types";

interface Props {
  job: JobListItem;
  onDelete: (id: string) => void;
}

export function JobCard({ job, onDelete }: Props) {
  const active = job.status === "pending" || job.status === "processing";
  const ws = useJobWebSocket(job.id, active);

  const status = ws.completed ? "completed" : job.status;
  const pct = ws.pct;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-gray-900">{job.video_filename}</p>
          <p className="mt-0.5 text-xs text-gray-500">
            {new Date(job.created_at).toLocaleString()} · {job.model_name}
            {job.language && ` · ${job.language}`}
          </p>
        </div>
        <ProgressBadge status={status} />
      </div>

      {active && pct > 0 && (
        <div className="mt-3">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-blue-500 transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-gray-500">
            {ws.step?.replace(/_/g, " ")} — {pct}%
          </p>
        </div>
      )}

      {ws.error && (
        <p className="mt-2 text-xs text-red-600">{ws.error}</p>
      )}

      <div className="mt-4 flex gap-2">
        {status === "completed" && (
          <Link
            href={`/jobs/${job.id}`}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
          >
            View transcript
          </Link>
        )}
        <button
          onClick={() => onDelete(job.id)}
          className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
