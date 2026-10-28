import { api } from "@/api/client";
import type { Question, QuestionIn, QType } from "@/api/quizzes";

export type SourceDoc = {
  id: string;
  kind: "file" | "url";
  name: string;
  tokenCount: number;
  chunks: number;
  preview: string;
  createdAt: string;
};

export type JobIn = {
  quizId: string;
  provider: string;
  model: string;
  strategy: "few_shot" | "zero_shot";
  mode: "material" | "topic";
  documentIds: string[];
  topic: string;
  focus: string;
  count: number;
  types: QType[];
  difficulty: number;
  language: "pl" | "en";
  temperature: number;
};

// pytanie w formacie zwracanym przez model
export type GenParsed = {
  question: string;
  type: QType;
  options?: { text: string; isCorrect: boolean }[];
  acceptedAnswers?: string[];
  explanation?: string;
  sourceQuote?: string;
  difficulty?: number;
  bloomLevel?: string;
  topic?: string;
};

export type GenQuestion = {
  id: string;
  idx: number;
  parsed: GenParsed;
  chunkText: string | null;
  grounded: boolean | null;
  groundingScore: number | null;
  duplicateOf: string | null;
  validationErrors: string[];
  status: "pending" | "accepted" | "edited" | "rejected" | "replaced";
};

export type Job = {
  id: string;
  quizId: string;
  sourceMode: string;
  strategy: string;
  provider: string;
  model: string;
  keySource: string;
  promptVersion: string;
  params: Record<string, unknown>;
  status: "queued" | "running" | "done" | "error";
  progress: number;
  calls: number;
  tokensIn: number;
  tokensOut: number;
  costUsd: number | null;
  durationMs: number;
  retries: number;
  error: string | null;
  createdAt: string;
  questions: GenQuestion[];
};

// materialy
export const listSources = () => api<SourceDoc[]>("/sources");
export function uploadSource(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api<SourceDoc>("/sources/upload", { form });
}
export const addSourceUrl = (url: string) => api<SourceDoc>("/sources/url", { json: { url } });
export const deleteSource = (id: string) => api<void>(`/sources/${id}`, { method: "DELETE" });

// generowanie
export const estimate = (data: JobIn) =>
  api<{ tokensIn: number; tokensOut: number; costUsd: number | null }>("/generation/estimate", {
    json: data,
  });
export const startJob = (data: JobIn) => api<Job>("/generation/jobs", { json: data });
export const getJob = (id: string) => api<Job>(`/generation/jobs/${id}`);
export const listJobs = (quizId: string) => api<Job[]>(`/generation/jobs?quizId=${quizId}`);

// recenzja
export const acceptGenerated = (id: string, edited?: QuestionIn) =>
  api<Question>(`/generated/${id}/accept`, edited ? { json: edited } : { method: "POST" });
export const rejectGenerated = (id: string) =>
  api<void>(`/generated/${id}/reject`, { method: "POST" });
export const regenerate = (id: string) =>
  api<GenQuestion>(`/generated/${id}/regenerate`, { method: "POST" });
export const acceptAll = (jobId: string) =>
  api<{ accepted: number }>(`/generation/jobs/${jobId}/accept-all`, { method: "POST" });
