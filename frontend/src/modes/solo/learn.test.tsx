import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Feedback, PlayQuestion } from "@/api/learn";
import { BoxBar } from "@/modes/solo/BoxBar";
import { LearnFeedback } from "@/modes/solo/LearnFeedback";
import { LearnQuestion } from "@/modes/solo/LearnQuestion";

const single: PlayQuestion = {
  id: "q1",
  type: "single",
  text: "Gdzie zachodzi fotosynteza?",
  media: null,
  options: [
    { id: "o1", text: "Mitochondria" },
    { id: "o2", text: "Chloroplasty" },
  ],
  box: null,
};

const wrong: Feedback = {
  correct: false,
  correctOptionIds: ["o2"],
  accepted: [],
  explanation: "Barwnik jest w chloroplastach.",
  sourceQuote: "Fotosynteza zachodzi w chloroplastach.",
  prevBox: 3,
  box: 1,
  answered: 1,
  correctCount: 0,
  stats: { total: 1, boxes: [0, 1, 0, 0, 0, 0], mastered: 0, masteredPct: 0 },
};

describe("nauka solo", () => {
  it("jednokrotny wybor wysyla odpowiedz od razu", () => {
    const onAnswer = vi.fn();
    render(<LearnQuestion q={single} feedback={null} busy={false} onAnswer={onAnswer} />);
    fireEvent.click(screen.getByRole("button", { name: /Chloroplasty/ }));
    expect(onAnswer).toHaveBeenCalledWith({ questionId: "q1", optionIds: ["o2"] });
  });

  it("wielokrotny wybor czeka na Sprawdz", () => {
    const onAnswer = vi.fn();
    const multi = { ...single, type: "multi" as const };
    render(<LearnQuestion q={multi} feedback={null} busy={false} onAnswer={onAnswer} />);
    fireEvent.click(screen.getByRole("button", { name: /Mitochondria/ }));
    fireEvent.click(screen.getByRole("button", { name: /Chloroplasty/ }));
    expect(onAnswer).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Sprawdź" }));
    expect(onAnswer).toHaveBeenCalledWith({ questionId: "q1", optionIds: ["o1", "o2"] });
  });

  it("po zlej odpowiedzi pokazuje poprawna, wyjasnienie, cytat i spadek pudelka", () => {
    render(<LearnFeedback q={single} f={wrong} />);
    expect(screen.getByText("Poprawna odpowiedź: Chloroplasty")).toBeInTheDocument();
    expect(screen.getByText("Barwnik jest w chloroplastach.")).toBeInTheDocument();
    expect(screen.getByText(/Fotosynteza zachodzi w chloroplastach/).tagName).toBe("BLOCKQUOTE");
    expect(screen.getByText(/Wraca do pudełka 1/)).toBeInTheDocument();
  });

  it("pasek pokazuje rozklad pudelek i opanowanie", () => {
    render(
      <BoxBar stats={{ total: 4, boxes: [1, 1, 0, 0, 1, 1], mastered: 2, masteredPct: 50 }} />,
    );
    expect(screen.getByText("opanowane 50%")).toBeInTheDocument();
    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("nowe: 1");
  });
});
