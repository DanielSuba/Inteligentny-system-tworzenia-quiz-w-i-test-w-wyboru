import type { Media } from "@/api/media";

// wyswietla media pytania: obraz, dzwiek, wideo albo film z YouTube (od-do sekundy)
export function MediaView({ media }: { media: Media }) {
  if (media.source === "youtube" && media.youtubeId) {
    const params = new URLSearchParams({ rel: "0" });
    if (media.startS != null) params.set("start", String(media.startS));
    if (media.endS != null) params.set("end", String(media.endS));
    return (
      <div className="aspect-video w-full max-w-xl border border-line shadow-ring">
        <iframe
          className="h-full w-full"
          src={`https://www.youtube-nocookie.com/embed/${media.youtubeId}?${params}`}
          title="YouTube"
          allow="encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }
  // fragment pliku: #t=start,koniec (obsluguja to przegladarki)
  const range =
    media.startS != null || media.endS != null
      ? `#t=${media.startS ?? 0}${media.endS != null ? "," + media.endS : ""}`
      : "";
  if (media.kind === "image") {
    return (
      <img
        src={media.url}
        alt=""
        className="max-h-80 max-w-full border border-line object-contain shadow-ring"
      />
    );
  }
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
