import type { Job, JobCreateResponse, JobListItem } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function createJob(
  file: File,
  language: string | null,
  model: string
): Promise<JobCreateResponse> {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams({ model });
  if (language) params.set("language", language);
  return request<JobCreateResponse>(`/api/v1/jobs?${params}`, {
    method: "POST",
    body: form,
  });
}

export async function listJobs(): Promise<JobListItem[]> {
  return request<JobListItem[]>("/api/v1/jobs");
}

export async function getJob(id: string): Promise<Job> {
  return request<Job>(`/api/v1/jobs/${id}`);
}

export async function deleteJob(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/v1/jobs/${id}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    throw new Error(`${res.status}: ${res.statusText}`);
  }
}

export function downloadUrl(id: string, format: "json" | "txt" | "srt"): string {
  return `${BASE_URL}/api/v1/jobs/${id}/download?format=${format}`;
}

export function videoUrl(filename: string): string {
  return `${BASE_URL}/uploads/${filename}`;
}

export function wsUrl(id: string): string {
  const wsBase = BASE_URL.replace(/^http/, "ws");
  return `${wsBase}/api/v1/jobs/${id}/ws`;
}
