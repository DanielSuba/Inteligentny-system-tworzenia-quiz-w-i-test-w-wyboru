import { useState } from "react";
import { useTranslation } from "react-i18next";
import { linkMedia, type Media, type MediaKind } from "@/api/media";
import { MediaView } from "@/components/quiz/MediaView";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { PixelIcon } from "@/components/ui/PixelIcon";
import type { IconName } from "@/components/ui/pixelIcons";
import { errorText } from "@/lib/errors";

type Props = { media: Media | null; onChange: (m: Media | null) => void };

const kinds: { kind: MediaKind; icon: IconName }[] = [
  { kind: "image", icon: "image" },
  { kind: "audio", icon: "note" },
  { kind: "video", icon: "film" },
];

// media pytania z linku: obraz, muzyka albo wideo (wgrywanie plikow w kolejnym etapie)
export function MediaField({ media, onChange }: Props) {
  const { t } = useTranslation("quiz");
  const [kind, setKind] = useState<MediaKind | null>(null);
  const [url, setUrl] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function close() {
    setKind(null);
    setUrl("");
    setStart("");
    setEnd("");
    setError("");
  }

  // dolacza media z linku
  async function attach() {
    if (!kind) return;
    setBusy(true);
    setError("");
    try {
      onChange(
        await linkMedia({
          kind,
          url: url.trim(),
          startS: start ? Number(start) : undefined,
          endS: end ? Number(end) : undefined,
        }),
      );
      close();
    } catch (e) {
      setError(errorText(e));
    }
    setBusy(false);
  }

  if (media) {
    return (
      <div className="flex flex-col gap-2">
        <span className="text-sm text-mut">{t(`media.${media.kind}`)}</span>
        <MediaView media={media} />
        <Button variant="ghost" className="self-start px-0" onClick={() => onChange(null)}>
          {t("media.remove")}
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div role="group" aria-label={t("media.label")} className="flex flex-wrap gap-2">
        {kinds.map((k) => (
          <Button
            key={k.kind}
            variant="secondary"
            aria-pressed={kind === k.kind}
            className={kind === k.kind ? "border-acc text-acc" : undefined}
            onClick={() => (kind === k.kind ? close() : setKind(k.kind))}
          >
            <PixelIcon name={k.icon} scale={1} />
            {t(`media.add_${k.kind}`)}
          </Button>
        ))}
      </div>

      {kind && (
        <div className="flex flex-col gap-3 border border-line bg-surf p-3">
          <Field
            label={t("media.url")}
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            hint={t(`media.hint_${kind}`)}
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
          {error && <Notice kind="error">{error}</Notice>}
          <div className="flex gap-2">
            <Button onClick={attach} busy={busy} disabled={!url.trim()}>
              {t("media.attach")}
            </Button>
            <Button variant="ghost" onClick={close}>
              {t("media.cancel")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
