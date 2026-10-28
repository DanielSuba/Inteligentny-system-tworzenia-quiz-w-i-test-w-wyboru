import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Media } from "@/api/media";
import { playerFor, type Ctl, type State } from "@/components/media/players";
import { PixelIcon } from "@/components/ui/PixelIcon";
import { fmtTime } from "@/lib/media";
import { cn } from "@/lib/utils";

type Props = {
  media: Media;
  hidden: boolean; // muzyka: gracz nie widzi odtwarzacza (obrazu, tytulu), tylko nasze przyciski
  onReady?: (ctl: Ctl) => void;
};

// odtwarzacz z serwisu (YouTube/SoundCloud/Spotify) z wlasnymi przyciskami i pilnowaniem fragmentu od-do
export function EmbedPlayer({ media, hidden, onReady }: Props) {
  const { t } = useTranslation("quiz");
  const box = useRef<HTMLDivElement>(null);
  const ctl = useRef<Ctl | null>(null);
  const [state, setState] = useState<State>({ playing: false, time: 0 });
  const [failed, setFailed] = useState(false);
  const start = media.startS ?? 0;
  const end = media.endS;

  useEffect(() => {
    const create = playerFor(media);
    if (!create || !box.current) return;
    let alive = true;
    create(media, box.current, (s) => {
      if (!alive) return;
      setState(s);
      // koniec fragmentu: zatrzymanie
      if (end && s.playing && s.time >= end) ctl.current?.pause();
    })
      .then((c) => {
        if (!alive) return c.destroy();
        ctl.current = c;
        onReady?.(c);
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
      ctl.current?.destroy();
      ctl.current = null;
    };
    // nowy odtwarzacz tylko przy zmianie utworu
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [media.id, media.source, media.url, media.youtubeId, media.embedId]);

  // przycisk odtworz/pauza; poza fragmentem wraca na jego poczatek
  function toggle() {
    const c = ctl.current;
    if (!c) return;
    if (state.playing) return c.pause();
    const now = c.time();
    if (now < start || (end && now >= end)) c.seek(start);
    c.play();
  }

  const shown = Math.max(0, state.time - start);
  const length = end ? end - start : null;

  return (
    <div className="flex flex-col gap-2">
      <div
        ref={box}
        aria-hidden={hidden}
        className={cn(
          hidden
            ? "pointer-events-none absolute -left-[10000px] top-0 h-[200px] w-[300px]"
            : media.kind === "audio"
              ? "h-[160px] w-full max-w-md"
              : "aspect-video w-full max-w-xl border border-line shadow-ring",
        )}
      />
      {hidden && (
        <div className="flex items-center gap-3 border border-line bg-surf2 px-3 py-2 shadow-ring">
          <button
            onClick={toggle}
            aria-label={state.playing ? t("media.pause") : t("media.play")}
            className="grid size-9 place-items-center bg-acc text-accfg"
          >
            <PixelIcon name={state.playing ? "pause" : "play"} scale={1} />
          </button>
          <PixelIcon name="note" scale={1} className="text-acc" />
          <span className="font-pixel text-[16px]">
            {fmtTime(shown)}
            {length ? ` / ${fmtTime(length)}` : ""}
          </span>
          {failed && <span className="text-sm text-bad">{t("media.playerError")}</span>}
        </div>
      )}
    </div>
  );
}
