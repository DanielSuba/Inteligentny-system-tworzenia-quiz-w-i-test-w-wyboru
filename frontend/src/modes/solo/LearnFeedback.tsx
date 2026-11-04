import { useTranslation } from "react-i18next";
import type { Feedback, PlayQuestion } from "@/api/learn";
import { Notice } from "@/components/ui/Notice";
import { boxColor } from "@/modes/solo/boxColor";

// informacja zwrotna po odpowiedzi: wynik, poprawna odpowiedz, wyjasnienie, cytat ze zrodla, pudelko
export function LearnFeedback({ q, f }: { q: PlayQuestion; f: Feedback }) {
  const { t } = useTranslation("learn");
  const answer =
    q.type === "open"
      ? f.accepted.join(" / ")
      : q.options
          .filter((o) => f.correctOptionIds.includes(o.id))
          .map((o) => o.text)
          .join(", ");

  return (
    <div className="flex flex-col gap-3">
      <Notice kind={f.correct ? "ok" : "error"}>
        <span className="font-bold">{f.correct ? t("good") : t("bad")}</span>{" "}
        {!f.correct && answer && t("correctWas", { answer })}
      </Notice>

      {f.explanation && (
        <div className="flex flex-col gap-1">
          <span className="pixel uppercase text-mut">{t("explanation")}</span>
          <p>{f.explanation}</p>
        </div>
      )}
      {f.sourceQuote && (
        <figure className="flex flex-col gap-1">
          <figcaption className="pixel uppercase text-mut">{t("source")}</figcaption>
          <blockquote className="border-l-2 border-acc pl-3 text-mut italic">
            „{f.sourceQuote}”
          </blockquote>
        </figure>
      )}

      <p className="flex items-center gap-2 text-sm text-mut">
        <i className="block size-2.5" style={{ background: boxColor[f.box] }} />
        {f.prevBox == null
          ? t("boxFirst", { box: f.box })
          : f.box > f.prevBox
            ? t("boxUp", { from: f.prevBox, box: f.box })
            : f.box < f.prevBox
              ? t("boxDown", { box: f.box })
              : t("boxSame", { box: f.box })}
      </p>
    </div>
  );
}
