import { useRef, useState, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { linkMedia, uploadMedia, type Media, type MediaKind } from "@/api/media";
import { MediaView } from "@/components/quiz/MediaView";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { cn } from "@/lib/utils";

type Props = { media: Media | null; onChange: (m: Media | null) => void };
type Mode = "closed" | "link" | "upload";

const kinds: MediaKind[] = ["image", "audio", "video"];

// wybor mediow do pytania: link (tez YouTube) albo wgranie pliku
export function MediaField({ media, onChange }: Props) {
  const { t } = useTranslation("quiz");
  const [mode, setMode] = useState<Mode>("closed");
  const [kind, setKind] = useState<MediaKind>("image");
  const [url, setUrl] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function done(m: Media) {
    onChange(m);
    setMode("closed");
    setUrl("");
    setStart("");
    setEnd("");
  }

  // dolacza media z linku
  async function attachLink() {
    setBusy(true);
    setError("");
    try {
      done(
        await linkMedia({
          kind,
          url: url.trim(),
          startS: start ? Number(start) : undefined,
          endS: end ? Number(end) : undefined,
        }),
      );
    } catch (e) {
      setError(errorText(e));
    }
    setBusy(false);
  }

  // wysyla wybrany plik
  async function pickFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      done(await uploadMedia(file, kind));
    } catch (err) {
      setError(errorText(err));
    }
    setBusy(false);
  }

  if (media) {
    return (
      <div className="flex flex-col gap-2">
        <span className="text-sm text-mut">{t("media.label")}</span>
        <MediaView media={media} />
        <Button variant="ghost" className="self-start px-0" onClick={() => onChange(null)}>
          {t("media.remove")}
        </Button>
      </div>
    );
  }

  if (mode === "closed") {
    return (
      <Button variant="secondary" className="self-start" onClick={() => setMode("link")}>
        {t("media.add")}
      </Button>
    );
  }

  const tab = (m: Mode) =>
    cn("border-b-2 px-3 py-1.5", mode === m ? "border-acc text-fg" : "border-transparent text-mut");

  return (
    <div className="flex flex-col gap-3 border border-line bg-surf p-3">
      <div className="flex gap-1" role="tablist">
        <button
          role="tab"
          aria-selected={mode === "link"}
          className={tab("link")}
          onClick={() => setMode("link")}
        >
          {t("media.link")}
        </button>
        <button
          role="tab"
          aria-selected={mode === "upload"}
          className={tab("upload")}
          onClick={() => setMode("upload")}
        >
          {t("media.upload")}
        </button>
      </div>
      <div role="group" aria-label={t("media.kind")} className="flex flex-wrap gap-2">
        {kinds.map((k) => (
          <button
            key={k}
            aria-pressed={kind === k}
            onClick={() => setKind(k)}
            className={cn(
              "border px-3 py-1 text-sm",
              kind === k ? "border-acc text-acc" : "border-line text-mut hover:text-fg",
            )}
          >
            {t(`media.${k}`)}
          </button>
        ))}
      </div>
      {mode === "link" ? (
        <>
          <Field
            label={t("media.url")}
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            hint={t("media.urlHint")}
          />
          {kind !== "image" && (
            <div className="grid grid-cols-2 gap-3">
              <Field
                label={t("media.start")}
                type="number"
                min={0}
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
              <Field
                label={t("media.end")}
                type="number"
                min={1}
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
          )}
          <div className="flex gap-2">
            <Button onClick={attachLink} busy={busy} disabled={!url.trim()}>
              {t("media.attach")}
            </Button>
            <Button variant="ghost" onClick={() => setMode("closed")}>
              {t("media.cancel")}
            </Button>
          </div>
        </>
      ) : (
        <>
          <input ref={fileRef} type="file" hidden accept={`${kind}/*`} onChange={pickFile} />
          <p className="text-sm text-mut">{t("media.limits")}</p>
          <div className="flex gap-2">
            <Button variant="secondary" busy={busy} onClick={() => fileRef.current?.click()}>
              {busy ? t("media.uploading") : t("media.file")}
            </Button>
            <Button variant="ghost" onClick={() => setMode("closed")}>
              {t("media.cancel")}
            </Button>
          </div>
        </>
      )}
      {error && <Notice kind="error">{error}</Notice>}
    </div>
  );
}
