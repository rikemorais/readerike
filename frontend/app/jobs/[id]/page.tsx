"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getJob } from "@/lib/api";
import { useJobWebSocket } from "@/hooks/useJobWebSocket";
import { ProgressBadge } from "@/components/ProgressBadge";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import type { Job } from "@/types";

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    getJob(id)
      .then(setJob)
      .catch((err) => setFetchError(err instanceof Error ? err.message : "Failed to load job"));
  }, [id]);

  const ws = useJobWebSocket(
    job?.status === "pending" || job?.status === "processing" ? id : null
  );

  useEffect(() => {
    if (ws.completed) setJob(ws.completed);
  }, [ws.completed]);

  if (fetchError) {
    return (
      <div className="space-y-4">
        <Link href="/" className="text-sm text-blue-600 hover:underline">← Back</Link>
        <p className="text-red-600">{fetchError}</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="space-y-4">
        <Link href="/" className="text-sm text-blue-600 hover:underline">← Back</Link>
        <p className="text-sm text-gray-500">Loading…</p>
      </div>
    );
  }

  const activeJob: Job =
    ws.completed ??
    (job.status === "processing" || job.status === "pending" ? job : job);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/" className="text-sm text-blue-600 hover:underline">← Back</Link>
        <h1 className="text-xl font-bold truncate flex-1">{activeJob.video_filename}</h1>
        <ProgressBadge status={activeJob.status} />
      </div>

      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        <div>
          <dt className="text-gray-500">Model</dt>
          <dd className="font-mono">{activeJob.model_name}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Language</dt>
          <dd className="font-mono">{activeJob.language ?? "auto-detect"}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Created</dt>
          <dd>{new Date(activeJob.created_at).toLocaleString()}</dd>
        </div>
        {activeJob.completed_at && (
          <div>
            <dt className="text-gray-500">Completed</dt>
            <dd>{new Date(activeJob.completed_at).toLocaleString()}</dd>
          </div>
        )}
      </dl>

      {(activeJob.status === "pending" || activeJob.status === "processing") && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-2">
          <p className="text-sm font-medium text-blue-800">
            {ws.step ?? "Waiting to start…"}
          </p>
          <div className="h-2 w-full rounded-full bg-blue-200 overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${ws.pct}%` }}
            />
          </div>
          <p className="text-xs text-blue-600">{ws.pct}%</p>
        </div>
      )}

      {activeJob.status === "failed" && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Transcription failed</p>
          {activeJob.error && (
            <pre className="mt-1 text-xs text-red-700 whitespace-pre-wrap">{activeJob.error}</pre>
          )}
        </div>
      )}

      {activeJob.status === "completed" && activeJob.transcription && (
        <TranscriptViewer job={activeJob} />
      )}
    </div>
  );
}
