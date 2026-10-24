import { api } from "@/api/client";
import type { Media } from "@/api/media";

export type QType = "single" | "multi" | "true_false" | "open";
export type Visibility = "public" | "unlisted" | "friends" | "private";
export type Lang = "pl" | "en";

export type Option = { id?: string; text: string; isCorrect: boolean };

export type Question = {
  id: string;
  position: number;
  type: QType;
  text: string;
  explanation: string;
  difficulty: number;
  timeLimitS: number | null;
  points: number | null;
  category: string | null;
  origin: string;
  sourceQuote: string | null;
  media: Media | null;
  options: Option[];
  accepted: string[];
  fuzzyThreshold: number;
  caseSensitive: boolean;
  ignoreAccents: boolean;
};

// dane wysylane przy zapisie pytania
export type QuestionIn = Omit<Question, "id" | "position" | "origin" | "sourceQuote" | "media"> & {
  mediaId: string | null;
};

export type Quiz = {
  id: string;
  title: string;
  description: string;
  language: Lang;
  visibility: Visibility;
  tags: string[];
  shareToken: string | null;
  cover: Media | null;
  isOwner: boolean;
  authorName: string;
  questionCount: number;
  createdAt: string;
  updatedAt: string;
};

export type QuizDetail = Quiz & { questions: Question[] };

export type QuizIn = {
  title: string;
  description?: string;
  language?: Lang;
  visibility?: Visibility;
  tags?: string[];
};

export function listQuizzes(q = "", visibility = "") {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (visibility) params.set("visibility", visibility);
  return api<Quiz[]>(`/quizzes?${params}`);
}

export const createQuiz = (data: QuizIn) => api<QuizDetail>("/quizzes", { json: data });
export const getQuiz = (id: string) => api<QuizDetail>(`/quizzes/${id}`);
export const getShared = (token: string) => api<QuizDetail>(`/shared/${token}`);
export const updateQuiz = (id: string, data: Partial<QuizIn>) =>
  api<QuizDetail>(`/quizzes/${id}`, { method: "PATCH", json: data });
export const deleteQuiz = (id: string) => api<void>(`/quizzes/${id}`, { method: "DELETE" });
export const newShareToken = (id: string) =>
  api<QuizDetail>(`/quizzes/${id}/share-token`, { method: "POST" });
export const reorderQuestions = (id: string, ids: string[]) =>
  api<QuizDetail>(`/quizzes/${id}/order`, { method: "PUT", json: { ids } });

export const addQuestion = (quizId: string, data: QuestionIn) =>
  api<Question>(`/quizzes/${quizId}/questions`, { json: data });
export const updateQuestion = (id: string, data: QuestionIn) =>
  api<Question>(`/questions/${id}`, { method: "PUT", json: data });
export const deleteQuestion = (id: string) => api<void>(`/questions/${id}`, { method: "DELETE" });
export const duplicateQuestion = (id: string) =>
  api<Question>(`/questions/${id}/duplicate`, { method: "POST" });

// sprawdzenie odpowiedzi otwartej na serwerze (token = podglad z linku)
export function checkOpenAnswer(id: string, odp: string, token?: string) {
  const query = token ? `?token=${encodeURIComponent(token)}` : "";
  return api<{ correct: boolean }>(`/questions/${id}/check${query}`, { json: { odp } });
}
