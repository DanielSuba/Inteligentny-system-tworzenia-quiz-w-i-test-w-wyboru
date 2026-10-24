import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { QuizDetail } from "@/api/quizzes";
import { changeType, emptyDraft, toPayload, validate } from "@/components/quiz/draft";
import { PreviewPlayer } from "@/components/quiz/PreviewPlayer";

const labels = { yes: "Prawda", no: "Fałsz" };

describe("walidacja pytania", () => {
  it("wymaga tresci i wypelnionych odpowiedzi", () => {
    const d = emptyDraft("single", labels);
    expect(validate(d)).toBe("errors.textRequired");
    expect(validate({ ...d, text: "Pytanie?" })).toBe("errors.optionEmpty");
  });

  it("jednokrotny wybor: dokladnie jedna poprawna", () => {
    const d = {
      ...emptyDraft("single", labels),
      text: "Pytanie?",
      options: [
        { text: "A", isCorrect: false },
        { text: "B", isCorrect: false },
      ],
    };
    expect(validate(d)).toBe("errors.oneCorrect");
    expect(validate({ ...d, options: [{ text: "A", isCorrect: true }, d.options[1]] })).toBeNull();
  });

  it("odpowiedzi musza sie roznic", () => {
    const d = {
      ...emptyDraft("multi", labels),
      text: "Pytanie?",
      options: [
        { text: "Tak", isCorrect: true },
        { text: " tak ", isCorrect: false },
      ],
    };
    expect(validate(d)).toBe("errors.optionsDuplicate");
  });

  it("zmiana typu na prawda/falsz i otwarte", () => {
    const tf = changeType(emptyDraft("single", labels), "true_false", labels);
    expect(tf.options.map((o) => o.text)).toEqual(["Prawda", "Fałsz"]);
    const open = {
      ...changeType(tf, "open", labels),
      text: "Stolica?",
      accepted: [" Warszawa ", ""],
    };
    expect(validate(open)).toBeNull();
    expect(toPayload(open)).toMatchObject({ type: "open", options: [], accepted: ["Warszawa"] });
  });
});

const quiz: QuizDetail = {
  id: "q1",
  title: "Chemia",
  description: "",
  language: "pl",
  visibility: "private",
  tags: [],
  shareToken: null,
  cover: null,
  isOwner: true,
  authorName: "Ania",
  questionCount: 1,
  createdAt: "2026-11-01T10:00:00Z",
  updatedAt: "2026-11-01T10:00:00Z",
  questions: [
    {
      id: "a",
      position: 0,
      type: "single",
      text: "Który pierwiastek ma symbol Fe?",
      explanation: "Ferrum.",
      difficulty: 2,
      timeLimitS: null,
      points: null,
      category: null,
      origin: "manual",
      sourceQuote: null,
      media: null,
      options: [
        { text: "Fluor", isCorrect: false },
        { text: "Żelazo", isCorrect: true },
      ],
      accepted: [],
      fuzzyThreshold: 85,
      caseSensitive: false,
      ignoreAccents: true,
    },
  ],
};

describe("podglad jako gracz", () => {
  it("pokazuje wynik po zlej odpowiedzi i podsumowanie", () => {
    render(<PreviewPlayer quiz={quiz} />);
    fireEvent.click(screen.getByRole("button", { name: /Fluor/ }));
    expect(screen.getByText(/Poprawna odpowiedź: Żelazo/)).toBeInTheDocument();
    expect(screen.getByText("Ferrum.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Zakończ" }));
    expect(screen.getByText("Poprawne odpowiedzi: 0 z 1")).toBeInTheDocument();
  });
});
