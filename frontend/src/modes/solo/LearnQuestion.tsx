import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import type { AnswerIn, Feedback, PlayQuestion } from "@/api/learn";
import { AnswerButton } from "@/components/quiz/AnswerButton";
import { MediaView } from "@/components/quiz/MediaView";
import { Button } from "@/components/ui/Button";

type Props = {
  q: PlayQuestion;
  feedback: Feedback | null; // po odpowiedzi: wynik z serwera
  busy: boolean;
  onAnswer: (a: AnswerIn) => void;
};

// pytanie w nauce: wybor odpowiedzi albo pole tekstowe; po odpowiedzi pokazuje poprawne
export function LearnQuestion({ q, feedback, busy, onAnswer }: Props) {
  const { t } = useTranslation("learn");
  const [picked, setPicked] = useState<string[]>([]);
  const [odp, setOdp] = useState("");
  const revealed = feedback !== null;

  // jednokrotny wybor wysyla od razu, wielokrotny po przycisku "Sprawdz"
  function pick(id: string) {
    if (revealed || busy) return;
    if (q.type === "multi") {
      setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));
    } else {
      setPicked([id]);
      onAnswer({ questionId: q.id, optionIds: [id] });
    }
  }

  function sendOpen(e: FormEvent) {
    e.preventDefault();
    if (odp.trim() && !revealed) onAnswer({ questionId: q.id, odp });
  }

  return (
    <div className="flex flex-col gap-5">
      <h2 className="text-2xl font-bold text-balance">{q.text}</h2>
      {q.media && <MediaView media={q.media} />}

      {q.type === "open" ? (
        <form onSubmit={sendOpen} className="flex flex-col gap-3 sm:flex-row">
          <input
            value={odp}
            onChange={(e) => setOdp(e.target.value)}
            disabled={revealed}
            autoFocus
            placeholder={t("answer")}
            aria-label={t("answer")}
            className="min-w-0 flex-1 border border-line bg-surf2 px-3 py-2 text-lg shadow-ring outline-none focus:border-acc"
          />
          {!revealed && (
            <Button type="submit" busy={busy}>
              {t("check")}
            </Button>
          )}
        </form>
      ) : (
        <>
          {q.type === "multi" && !revealed && <p className="text-sm text-mut">{t("multiHint")}</p>}
          <div className="grid gap-3 sm:grid-cols-2">
            {q.options.map((o, i) => (
              <AnswerButton
                key={o.id}
                i={i}
                text={o.text}
                picked={picked.includes(o.id)}
                revealed={revealed}
                good={!!feedback?.correctOptionIds.includes(o.id)}
                onClick={() => pick(o.id)}
              />
            ))}
          </div>
          {q.type === "multi" && !revealed && (
            <Button
              className="self-start"
              busy={busy}
              disabled={!picked.length}
              onClick={() => onAnswer({ questionId: q.id, optionIds: picked })}
            >
              {t("check")}
            </Button>
          )}
        </>
      )}
    </div>
  );
}
