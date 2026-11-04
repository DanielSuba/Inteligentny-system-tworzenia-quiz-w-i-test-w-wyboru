import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { updateMedia, type Media, type MediaUpdate } from "@/api/media";
import { CropEditor } from "@/components/media/CropEditor";
import { EmbedPlayer } from "@/components/media/EmbedPlayer";
import type { Ctl } from "@/components/media/players";
import { MediaView } from "@/components/quiz/MediaView";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { errorText } from "@/lib/errors";
import { fmtTime, parseTime } from "@/lib/media";

type Props = { media: Media; onChange: (m: Media) => void };

const box =
  "w-24 border border-line bg-surf2 px-2 py-1.5 font-pixel text-[16px] shadow-ring outline-none focus:border-acc";

// ustawienia mediow w edytorze: kadr i wielkosc obrazu, fragment muzyki/wideo, ukrycie obrazu
export function MediaSettings({ media, onChange }: Props) {
  const { t } = useTranslation("quiz");
  const [cropping, setCropping] = useState(false);
  const [start, setStart] = useState(media.startS != null ? fmtTime(media.startS) : "");
  const [end, setEnd] = useState(media.endS != null ? fmtTime(media.endS) : "");
  const [error, setError] = useState("");
  const player = useRef<Ctl | null>(null);
  const fileEl = useRef<HTMLMediaElement | null>(null);

  async function save(data: MediaUpdate) {
    setError("");
    try {
      onChange(await updateMedia(media.id, data));
    } catch (e) {
      setError(errorText(e));
    }
  }

  // aktualny czas odtwarzacza (do przyciskow "ustaw tutaj")
  const now = () => Math.floor(player.current?.time() ?? fileEl.current?.currentTime ?? 0);

  function saveRange() {
    const s = parseTime(start);
    const e = parseTime(end);
    if (Number.isNaN(s) || Number.isNaN(e) || (s != null && e != null && e <= s)) {
      return setError(t("media.badRange"));
    }
    save({ startS: s, endS: e });
  }

  if (media.kind === "image") {
    return (
      <div className="flex flex-col gap-3">
        {cropping ? (
          <CropEditor
            url={media.url}
            onCancel={() => setCropping(false)}
            onSave={async (crop) => {
              await save({ crop });
              setCropping(false);
            }}
          />
        ) : (
          <MediaView media={media} />
        )}
        <div className="flex flex-wrap items-center gap-3">
          {!cropping && (
            <Button variant="secondary" onClick={() => setCropping(true)}>
              {t("media.crop")}
            </Button>
          )}
          <label className="flex items-center gap-2 text-sm text-mut">
            {t("media.size", { v: media.displayWidth ?? 100 })}
            <input
              type="range"
              min={20}
              max={100}
              step={5}
              defaultValue={media.displayWidth ?? 100}
              onMouseUp={(e) => save({ displayWidth: Number(e.currentTarget.value) })}
              onTouchEnd={(e) => save({ displayWidth: Number(e.currentTarget.value) })}
              onKeyUp={(e) => save({ displayWidth: Number(e.currentTarget.value) })}
              className="accent-[var(--acc)]"
            />
          </label>
        </div>
        {error && <Notice kind="error">{error}</Notice>}
      </div>
    );
  }

  const embed =
    media.source === "youtube" || media.source === "soundcloud" || media.source === "spotify";
  return (
    <div className="flex flex-col gap-3">
      {/* autor w edytorze widzi odtwarzacz, zeby wybrac moment startu */}
      {embed ? (
        <EmbedPlayer
          key={media.id}
          media={media}
          hidden={false}
          onReady={(c) => (player.current = c)}
        />
      ) : media.kind === "audio" ? (
        <audio
          ref={(el) => void (fileEl.current = el)}
          controls
          preload="metadata"
          src={media.url}
          className="w-full max-w-xl"
        />
      ) : (
        <video
          ref={(el) => void (fileEl.current = el)}
          controls
          preload="metadata"
          src={media.url}
          className="max-h-72 w-full max-w-xl border border-line"
        />
      )}
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm text-mut">
          {t("media.start")}
          <span className="flex gap-1">
            <input
              value={start}
              onChange={(e) => setStart(e.target.value)}
              placeholder="0:00"
              className={box}
            />
            <Button
              variant="secondary"
              className="px-2 py-1 text-sm"
              onClick={() => setStart(fmtTime(now()))}
            >
              {t("media.here")}
            </Button>
          </span>
        </label>
        <label className="flex flex-col gap-1 text-sm text-mut">
          {t("media.end")}
          <span className="flex gap-1">
            <input
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              placeholder="—"
              className={box}
            />
            <Button
              variant="secondary"
              className="px-2 py-1 text-sm"
              onClick={() => setEnd(fmtTime(now()))}
            >
              {t("media.here")}
            </Button>
          </span>
        </label>
        <Button onClick={saveRange}>{t("media.saveRange")}</Button>
      </div>
      {media.source === "youtube" && media.kind === "audio" && (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={media.hideVideo}
            onChange={(e) => save({ hideVideo: e.target.checked })}
            className="size-4 accent-[var(--acc)]"
          />
          {t("media.hideVideo")}
        </label>
      )}
      {(media.source === "spotify" || media.source === "soundcloud" || media.hideVideo) && (
        <p className="text-sm text-mut">
          {t(media.source === "spotify" ? "media.spotifyNote" : "media.hiddenNote")}
        </p>
      )}
      {error && <Notice kind="error">{error}</Notice>}
    </div>
  );
}
