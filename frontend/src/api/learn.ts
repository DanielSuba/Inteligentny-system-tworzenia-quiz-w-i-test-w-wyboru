import { api } from "@/api/client";
import type { Media } from "@/api/media";
import type { QType } from "@/api/quizzes";

// boxes[0] = niewidziane, boxes[1..5] = pudelka Leitnera
export type LearnStats = { total: number; boxes: number[]; mastered: number; masteredPct: number };

export type LearnSession = {
  id: string;
  quizId: string;
  quizTitle: string;
  startedAt: string;
  endedAt: string | null;
  answered: number;
  correct: number;
  stats: LearnStats;
};

// pytanie bez poprawnych odpowiedzi (sprawdza serwer)
export type PlayQuestion = {
  id: string;
  type: QType;
  text: string;
  media: Media | null;
  options: { id: string; text: string }[];
  box: number | null;
};

export type AnswerIn = { questionId: string; optionIds?: string[]; odp?: string };

export type Feedback = {
  correct: boolean;
  correctOptionIds: string[];
  accepted: string[];
  explanation: string;
  sourceQuote: string | null;
  prevBox: number | null;
  box: number;
  answered: number;
  correctCount: number;
  stats: LearnStats;
};

export const startLearning = (quizId: string, token?: string | null) =>
  api<LearnSession>("/learn/sessions", { json: { quizId, token: token || null } });

export const nextQuestion = (sessionId: string) =>
  api<{ question: PlayQuestion | null; stats: LearnStats }>(`/learn/sessions/${sessionId}/next`);

export const sendAnswer = (sessionId: string, data: AnswerIn) =>
  api<Feedback>(`/learn/sessions/${sessionId}/answer`, { json: data });

export const endLearning = (sessionId: string) =>
  api<LearnSession>(`/learn/sessions/${sessionId}/end`, { method: "POST" });

const tokenQuery = (token?: string | null) => (token ? `?token=${encodeURIComponent(token)}` : "");

export const learnProgress = (quizId: string, token?: string | null) =>
  api<LearnStats>(`/learn/quizzes/${quizId}/progress${tokenQuery(token)}`);

export const resetLearning = (quizId: string, token?: string | null) =>
  api<void>(`/learn/quizzes/${quizId}/progress${tokenQuery(token)}`, { method: "DELETE" });
