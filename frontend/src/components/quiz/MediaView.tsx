import type { Media } from "@/api/media";
import { CroppedImage } from "@/components/media/CroppedImage";
import { EmbedPlayer } from "@/components/media/EmbedPlayer";
import { isHiddenMusic } from "@/lib/media";

// wyswietla media pytania: obraz (z kadrem), muzyke, wideo; fragment od-do
export function MediaView({ media }: { media: Media }) {
  if (media.source === "youtube" || media.source === "soundcloud" || media.source === "spotify") {
    // key: nowy utwor = nowy odtwarzacz z czystym stanem (czas, pauza)
    return <EmbedPlayer key={media.id} media={media} hidden={isHiddenMusic(media)} />;
  }
  if (media.kind === "image") return <CroppedImage media={media} />;
  // fragment pliku: #t=start,koniec (obsluguja to przegladarki)
  const range =
    media.startS != null || media.endS != null
      ? `#t=${media.startS ?? 0}${media.endS != null ? "," + media.endS : ""}`
      : "";
  if (media.kind === "audio") {
    return (
      <audio controls preload="metadata" src={media.url + range} className="w-full max-w-xl" />
    );
  }
  return (
    <video
      controls
      preload="metadata"
      src={media.url + range}
      className="max-h-80 w-full max-w-xl border border-line shadow-ring"
    />
  );
}
