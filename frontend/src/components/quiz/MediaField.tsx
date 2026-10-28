import { useRef, useState, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { linkMedia, uploadMedia, type Media, type MediaKind } from "@/api/media";
import { MediaSettings } from "@/components/media/MediaSettings";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { PixelIcon } from "@/components/ui/PixelIcon";
import type { IconName } from "@/components/ui/pixelIcons";
import { errorText } from "@/lib/errors";
import { cn } from "@/lib/utils";

type Props = { media: Media | null; onChange: (m: Media | null) => void };
type Mode = "link" | "upload";

const kinds: { kind: MediaKind; icon: IconName }[] = [
  { kind: "image", icon: "image" },
  { kind: "audio", icon: "note" },
  { kind: "video", icon: "film" },
];

// media pytania: obraz, muzyka albo wideo; z linku albo z pliku; potem ustawienia (kadr, fragment)
export function MediaField({ media, onChange }: Props) {
  const { t } = useTranslation("quiz");
  const [kind, setKind] = useState<MediaKind | null>(null);
  const [mode, setMode] = useState<Mode>("link");
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function close() {
    setKind(null);
    setUrl("");
    setError("");
  }

  // dolacza media (link albo wgrany plik)
  async function attach(make: () => Promise<Media>) {
    setBusy(true);
    setError("");
    try {
      onChange(await make());
      close();
    } catch (e) {
      setError(errorText(e));
    }
    setBusy(false);
  }

  function pickFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file && kind) attach(() => uploadMedia(file, kind));
  }

  if (media) {
    return (
      <div className="flex flex-col gap-3">
        <span className="text-sm text-mut">{t(`media.${media.kind}`)}</span>
        <MediaSettings key={media.id} media={media} onChange={onChange} />
        <Button variant="ghost" className="self-start px-0" onClick={() => onChange(null)}>
          {t("media.remove")}
        </Button>
      </div>
    );
  }

  const tab = (m: Mode) =>
    cn(
      "border-b-2 px-3 py-1.5",
      mode === m ? "border-acc text-fg" : "border-transparent text-mut hover:text-fg",
    );

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
          {mode === "link" ? (
            <Field
              label={t("media.url")}
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              hint={t(`media.hint_${kind}`)}
            />
          ) : (
            <>
              <input ref={fileRef} type="file" hidden accept={`${kind}/*`} onChange={pickFile} />
              <p className="text-sm text-mut">{t("media.limits")}</p>
            </>
          )}
          {error && <Notice kind="error">{error}</Notice>}
          <div className="flex gap-2">
            {mode === "link" ? (
              <Button
                onClick={() => attach(() => linkMedia({ kind, url: url.trim() }))}
                busy={busy}
                disabled={!url.trim()}
              >
                {t("media.attach")}
              </Button>
            ) : (
              <Button busy={busy} onClick={() => fileRef.current?.click()}>
                <PixelIcon name="upload" scale={1} />
                {busy ? t("media.uploading") : t("media.file")}
              </Button>
            )}
            <Button variant="ghost" onClick={close}>
              {t("media.cancel")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
