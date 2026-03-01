"use client";

import { useCallback, useEffect, useState } from "react";
import { deleteJob, listJobs } from "@/lib/api";
import { VideoUpload } from "@/components/VideoUpload";
import { JobCard } from "@/components/JobCard";
import type { JobListItem } from "@/types";

export default function HomePage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const data = await listJobs();
      setJobs(data.sort((a, b) => b.created_at.localeCompare(a.created_at)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleDelete = useCallback(async (id: string) => {
    await deleteJob(id);
    setJobs((prev) => prev.filter((j) => j.id !== id));
  }, []);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold mb-4">New transcription</h1>
        <VideoUpload onCreated={fetchJobs} />
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Jobs</h2>

        {loading && (
          <p className="text-sm text-gray-500">Loading…</p>
        )}

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        {!loading && jobs.length === 0 && (
          <p className="text-sm text-gray-500">No jobs yet. Upload a video above.</p>
        )}

        <ul className="space-y-3">
          {jobs.map((job) => (
            <li key={job.id}>
              <JobCard job={job} onDelete={handleDelete} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
