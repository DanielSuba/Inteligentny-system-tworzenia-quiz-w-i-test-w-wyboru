import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { GenQuestion } from "@/api/generation";
import type { QuestionIn } from "@/api/quizzes";
import { answerColor, letters, shapes } from "@/components/quiz/answerLook";
import { fromGenerated, toPayload, validate, type Draft } from "@/components/quiz/draft";
import { QuestionEditor } from "@/components/quiz/QuestionEditor";
import { Button } from "@/components/ui/Button";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { cn } from "@/lib/utils";

type Props = {
  g: GenQuestion;
  onAccept: (edited?: QuestionIn) => Promise<void>;
  onReject: () => Promise<void>;
  onRegenerate: () => Promise<void>;
};

// fragment zrodla z podswietlonym cytatem (jesli da sie go znalezc)
function Highlighted({ text, quote }: { text: string; quote: string }) {
  const at = quote ? text.toLowerCase().indexOf(quote.toLowerCase().trim()) : -1;
  if (at < 0) return <>{text}</>;
  const end = at + quote.trim().length;
  return (
    <>
      {text.slice(0, at)}
      <mark className="bg-[color-mix(in_srgb,var(--acc)_35%,transparent)] text-fg">
        {text.slice(at, end)}
      </mark>
      {text.slice(end)}
    </>
  );
}

// jedno wygenerowane pytanie: tresc, oznaczenia z automatycznych sprawdzen, decyzja recenzenta
export function GeneratedCard({ g, onAccept, onReject, onRegenerate }: Props) {
  const { t } = useTranslation(["generate", "quiz"]);
  const [editing, setEditing] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const p = g.parsed;
  const done = g.status !== "pending";

  async function run(action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
    } finally {
      setBusy(false);
    }
  }

  if (editing) {
    return (
      <li className="border-b border-line py-4">
        <QuestionEditor
          draft={editing}
          onChange={setEditing}
          saving={busy}
          msg={err ? { kind: "error", text: err } : null}
          saveLabel={t("review.acceptEdited")}
          onSave={() => {
            const bad = validate(editing);
            if (bad) return setErr(t(`quiz:${bad}`));
            run(() => onAccept(toPayload(editing)));
          }}
          onDuplicate={() => null}
          onDelete={() => setEditing(null)}
          deleteLabel={t("review.cancel")}
        />
      </li>
    );
  }

  return (
    <li className={cn("flex flex-col gap-3 border-b border-line py-4", done && "opacity-60")}>
      <div className="flex flex-wrap items-baseline gap-2">
        <span className="font-pixel text-[12px] text-mut">{g.idx + 1}.</span>
        <span className="text-sm text-mut">
          {t(`quiz:types.${p.type}`)}
          {p.bloomLevel &&
            ` · ${t(`review.bloom.${p.bloomLevel}`, { defaultValue: p.bloomLevel })}`}
        </span>
        {done && <span className="pixel text-acc">{t(`review.status_${g.status}`)}</span>}
      </div>
      <p className="text-lg font-bold">{p.question}</p>

      {p.type === "open" ? (
        <p className="text-sm">
          <span className="text-mut">{t("review.accepted")}: </span>
          {(p.acceptedAnswers ?? []).join(", ")}
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {(p.options ?? []).map((o, i) => (
            <li
              key={i}
              className={cn("flex items-center gap-2", o.isCorrect ? "text-fg" : "text-mut")}
            >
              <span style={{ color: answerColor(i) }}>
                <PixelIcon name={shapes[i % 10]} scale={1} />
              </span>
              <span className="font-pixel text-[12px]">{letters[i]}</span>
              {o.text}
              {o.isCorrect && (
                <span className="text-ok">
                  <PixelIcon name="check" scale={1} />
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
      {p.explanation && <p className="text-sm text-mut">{p.explanation}</p>}

      <div className="flex flex-wrap gap-2 text-sm">
        {g.grounded === true && (
          <span className="border border-ok px-2 text-ok">{t("review.quoteFound")}</span>
        )}
        {g.grounded === false && (
          <span className="border border-bad px-2 text-bad">{t("review.quoteMissing")}</span>
        )}
        {g.duplicateOf && (
          <span className="border border-acc px-2 text-acc">
            {t("review.duplicate", { q: g.duplicateOf })}
          </span>
        )}
        {g.validationErrors.length > 0 && (
          <span className="border border-bad px-2 text-bad" title={g.validationErrors.join("; ")}>
            {t("review.invalid")}: {g.validationErrors.join("; ")}
          </span>
        )}
      </div>

      {g.chunkText && (
        <details>
          <summary className="cursor-pointer text-sm text-mut hover:text-fg">
            {t("review.source")}
          </summary>
          <p className="mt-2 max-h-60 overflow-auto border-l-2 border-line pl-3 text-sm whitespace-pre-line text-mut">
            <Highlighted text={g.chunkText} quote={p.sourceQuote ?? ""} />
          </p>
        </details>
      )}
      {!g.chunkText && p.sourceQuote && (
        <p className="text-sm text-mut">
          {t("review.quote")}: „{p.sourceQuote}”
        </p>
      )}

      {!done && (
        <div className="flex flex-wrap gap-2">
          <Button
            busy={busy}
            disabled={g.validationErrors.length > 0}
            onClick={() => run(() => onAccept())}
          >
            {t("review.accept")}
          </Button>
          <Button variant="secondary" onClick={() => setEditing(fromGenerated(p))}>
            {t("review.edit")}
          </Button>
          <Button variant="secondary" busy={busy} onClick={() => run(onRegenerate)}>
            {t("review.regenerate")}
          </Button>
          <Button variant="ghost" className="hover:text-bad" onClick={() => run(onReject)}>
            {t("review.reject")}
          </Button>
        </div>
      )}
    </li>
  );
}
