import type { Media } from "@/api/media";
import type { Option, QType, Question, QuestionIn } from "@/api/quizzes";

// pytanie w trakcie edycji (liczby jako tekst, bo to pola formularza)
export type Draft = {
  id?: string;
  type: QType;
  text: string;
  explanation: string;
  difficulty: number;
  timeLimitS: string;
  points: string;
  category: string;
  media: Media | null;
  options: Option[];
  accepted: string[];
  fuzzyThreshold: number;
  caseSensitive: boolean;
  ignoreAccents: boolean;
};

type Labels = { yes: string; no: string };

export function toDraft(q: Question): Draft {
  return {
    id: q.id,
    type: q.type,
    text: q.text,
    explanation: q.explanation,
    difficulty: q.difficulty,
    timeLimitS: q.timeLimitS?.toString() ?? "",
    points: q.points?.toString() ?? "",
    category: q.category ?? "",
    media: q.media,
    options: q.options.map((o) => ({ text: o.text, isCorrect: o.isCorrect })),
    accepted: q.accepted.length ? q.accepted : [""],
    fuzzyThreshold: q.fuzzyThreshold,
    caseSensitive: q.caseSensitive,
    ignoreAccents: q.ignoreAccents,
  };
}

const blankOptions = (n: number): Option[] =>
  Array.from({ length: n }, () => ({ text: "", isCorrect: false }));

export function emptyDraft(type: QType, labels: Labels): Draft {
  return changeType(
    {
      type: "single",
      text: "",
      explanation: "",
      difficulty: 2,
      timeLimitS: "",
      points: "",
      category: "",
      media: null,
      options: blankOptions(4),
      accepted: [""],
      fuzzyThreshold: 85,
      caseSensitive: false,
      ignoreAccents: true,
    },
    type,
    labels,
  );
}

// zmiana typu pytania z zachowaniem tego, co sie da
export function changeType(d: Draft, type: QType, labels: Labels): Draft {
  if (type === "true_false") {
    return {
      ...d,
      type,
      options: [
        { text: labels.yes, isCorrect: true },
        { text: labels.no, isCorrect: false },
      ],
    };
  }
  if (type === "open") return { ...d, type, accepted: d.accepted.length ? d.accepted : [""] };

  let options = d.type === "true_false" || d.type === "open" ? blankOptions(4) : d.options;
  if (type === "single") {
    // przy jednokrotnym wyborze zostaje najwyzej jedna poprawna
    const first = options.findIndex((o) => o.isCorrect);
    options = options.map((o, i) => ({ ...o, isCorrect: i === first }));
  }
  return { ...d, type, options };
}

// sprawdza pytanie przed zapisem; zwraca klucz bledu albo null
export function validate(d: Draft): string | null {
  if (!d.text.trim()) return "errors.textRequired";
  if (d.type === "open") {
    return d.accepted.some((a) => a.trim()) ? null : "errors.acceptedMin";
  }
  if (d.options.length < 2) return "errors.optionsMin";
  if (d.options.some((o) => !o.text.trim())) return "errors.optionEmpty";
  const texts = d.options.map((o) => o.text.trim().toLowerCase());
  if (new Set(texts).size !== texts.length) return "errors.optionsDuplicate";
  const good = d.options.filter((o) => o.isCorrect).length;
  if (d.type !== "multi" && good !== 1) return "errors.oneCorrect";
  if (d.type === "multi" && good < 1) return "errors.someCorrect";
  return null;
}

const num = (s: string) => (s.trim() ? Number(s) : null);

export function toPayload(d: Draft): QuestionIn {
  const isOpen = d.type === "open";
  return {
    type: d.type,
    text: d.text.trim(),
    explanation: d.explanation.trim(),
    difficulty: d.difficulty,
    timeLimitS: num(d.timeLimitS),
    points: num(d.points),
    category: d.category.trim() || null,
    mediaId: d.media?.id ?? null,
    options: isOpen ? [] : d.options.map((o) => ({ text: o.text.trim(), isCorrect: o.isCorrect })),
    accepted: isOpen ? d.accepted.map((a) => a.trim()).filter(Boolean) : [],
    fuzzyThreshold: d.fuzzyThreshold,
    caseSensitive: d.caseSensitive,
    ignoreAccents: d.ignoreAccents,
  };
}
