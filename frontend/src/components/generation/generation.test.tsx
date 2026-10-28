import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { GenQuestion } from "@/api/generation";
import type { Media } from "@/api/media";
import { GeneratedCard } from "@/components/generation/GeneratedCard";
import { fromGenerated, validate } from "@/components/quiz/draft";
import { fmtTime, isHiddenMusic, parseTime } from "@/lib/media";

const g: GenQuestion = {
  id: "g1",
  idx: 0,
  parsed: {
    question: "Gdzie zachodzi fotosynteza?",
    type: "single",
    options: [
      { text: "Mitochondria", isCorrect: false },
      { text: "Chloroplasty", isCorrect: true },
    ],
    explanation: "W chloroplastach.",
    sourceQuote: "zachodzi w chloroplastach",
    bloomLevel: "remember",
  },
  chunkText: "Fotosynteza zachodzi w chloroplastach komórek roślinnych.",
  grounded: true,
  groundingScore: 100,
  duplicateOf: null,
  validationErrors: [],
  status: "pending",
};

describe("recenzja pytania z AI", () => {
  it("pokazuje oznaczenia i przyjmuje pytanie", () => {
    const onAccept = vi.fn().mockResolvedValue(undefined);
    render(<GeneratedCard g={g} onAccept={onAccept} onReject={vi.fn()} onRegenerate={vi.fn()} />);
    expect(screen.getByText("cytat znaleziony w materiale")).toBeInTheDocument();
    expect(screen.getByText("zachodzi w chloroplastach").tagName).toBe("MARK");
    fireEvent.click(screen.getByRole("button", { name: "Przyjmij" }));
    expect(onAccept).toHaveBeenCalledWith();
  });

  it("pytania z bledem nie da sie przyjac bez poprawki", () => {
    const bad = { ...g, grounded: false, validationErrors: ["dokladnie 1 poprawna"] };
    render(<GeneratedCard g={bad} onAccept={vi.fn()} onReject={vi.fn()} onRegenerate={vi.fn()} />);
    expect(screen.getByText("cytatu nie ma w materiale")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Przyjmij" })).toBeDisabled();
  });

  it("zamienia pytanie z modelu na szkic edytora", () => {
    const d = fromGenerated({ question: "Barwnik?", type: "open", acceptedAnswers: ["chlorofil"] });
    expect(d.accepted).toEqual(["chlorofil"]);
    expect(validate(d)).toBeNull();
  });
});

describe("czas i muzyka", () => {
  it("czyta i formatuje czas", () => {
    expect(parseTime("1:05")).toBe(65);
    expect(parseTime("90")).toBe(90);
    expect(parseTime("")).toBeNull();
    expect(parseTime("1:75")).toBeNaN();
    expect(fmtTime(65)).toBe("1:05");
  });

  it("muzyka z serwisow jest ukryta, wideo nie", () => {
    const base = { kind: "audio", source: "youtube", hideVideo: true } as Media;
    expect(isHiddenMusic(base)).toBe(true);
    expect(isHiddenMusic({ ...base, hideVideo: false })).toBe(false);
    expect(isHiddenMusic({ ...base, source: "spotify", hideVideo: false })).toBe(true);
    expect(isHiddenMusic({ ...base, kind: "video" })).toBe(false);
  });
});
