/* eslint-disable @typescript-eslint/no-explicit-any */
import type { Media } from "@/api/media";

// wspolne sterowanie odtwarzaczami z serwisow (YouTube, SoundCloud, Spotify)
export type Ctl = {
  play: () => void;
  pause: () => void;
  seek: (s: number) => void;
  time: () => number;
  destroy: () => void;
};
export type State = { playing: boolean; time: number };

const w = window as any;
const loading: Record<string, Promise<void>> = {};

// laduje skrypt zewnetrzny tylko raz
function loadScript(src: string): Promise<void> {
  loading[src] ??= new Promise((ok, fail) => {
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = () => ok();
    s.onerror = () => fail(new Error("script"));
    document.head.appendChild(s);
  });
  return loading[src];
}

// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// @@@@@@@@@@@@@@@@ YouTube @@@@@@@@@@@@@@@@
// @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

const ytReady = () =>
  new Promise<void>((ok) => {
    if (w.YT?.Player) return ok();
    const prev = w.onYouTubeIframeAPIReady;
    w.onYouTubeIframeAPIReady = () => {
      prev?.();
      ok();
    };
    loadScript("https://www.youtube.com/iframe_api");
  });

async function youtube(m: Media, box: HTMLElement, onState: (s: State) => void): Promise<Ctl> {
  await ytReady();
  const el = document.createElement("div");
  box.appendChild(el);
  let player: any;
  await new Promise<void>((ok) => {
    player = new w.YT.Player(el, {
      videoId: m.youtubeId,
      width: "100%",
      height: "100%",
      host: "https://www.youtube-nocookie.com",
      playerVars: { start: m.startS ?? 0, end: m.endS ?? undefined, rel: 0, playsinline: 1 },
      events: { onReady: () => ok() },
    });
  });
  const timer = setInterval(
    () =>
      onState({ playing: player.getPlayerState?.() === 1, time: player.getCurrentTime?.() ?? 0 }),
    250,
  );
  return {
    play: () => player.playVideo(),
    pause: () => player.pauseVideo(),
    seek: (s) => player.seekTo(s, true),
    time: () => player.getCurrentTime?.() ?? 0,
    destroy: () => {
      clearInterval(timer);
      player.destroy?.();
    },
  };
}

// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
// $$$$$$$$$$$$$$$ SoundCloud $$$$$$$$$$$$$$$
// $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

async function soundcloud(m: Media, box: HTMLElement, onState: (s: State) => void): Promise<Ctl> {
  await loadScript("https://w.soundcloud.com/player/api.js");
  const frame = document.createElement("iframe");
  frame.allow = "autoplay";
  frame.style.cssText = "width:100%;height:100%;border:0";
  frame.src = `https://w.soundcloud.com/player/?url=${encodeURIComponent(m.url)}&auto_play=false&visual=false`;
  box.appendChild(frame);
  const widget = w.SC.Widget(frame);
  let now = 0;
  let playing = false;
  await new Promise<void>((ok) => widget.bind(w.SC.Widget.Events.READY, () => ok()));
  const update = () => onState({ playing, time: now });
  widget.bind(w.SC.Widget.Events.PLAY_PROGRESS, (e: any) => {
    now = e.currentPosition / 1000;
    update();
  });
  widget.bind(w.SC.Widget.Events.PLAY, () => ((playing = true), update()));
  widget.bind(w.SC.Widget.Events.PAUSE, () => ((playing = false), update()));
  widget.bind(w.SC.Widget.Events.FINISH, () => ((playing = false), update()));
  return {
    play: () => widget.play(),
    pause: () => widget.pause(),
    seek: (s) => widget.seekTo(s * 1000),
    time: () => now,
    destroy: () => frame.remove(),
  };
}

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
// %%%%%%%%%%%%%%%% Spotify %%%%%%%%%%%%%%%%
// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

let spotifyApi: Promise<any> | null = null;
const spotifyReady = () => {
  spotifyApi ??= new Promise((ok) => {
    w.onSpotifyIframeApiReady = (api: any) => ok(api);
    loadScript("https://open.spotify.com/embed/iframe-api/v1");
  });
  return spotifyApi;
};

// Spotify bez zalogowania odtwarza tylko 30-sekundowy podglad
async function spotify(m: Media, box: HTMLElement, onState: (s: State) => void): Promise<Ctl> {
  const api = await spotifyReady();
  const el = document.createElement("div");
  box.appendChild(el);
  let now = 0;
  let playing = false;
  const ctrl: any = await new Promise((ok) =>
    api.createController(
      el,
      { uri: `spotify:${(m.embedId ?? "").replace("/", ":")}`, width: "100%", height: 152 },
      ok,
    ),
  );
  ctrl.addListener("playback_update", (e: any) => {
    now = e.data.position / 1000;
    playing = !e.data.isPaused;
    onState({ playing, time: now });
  });
  // resume/pause zamiast togglePlay: seek sam wlacza granie, a przelacznik by je wtedy zatrzymal
  return {
    play: () => ctrl.resume(),
    pause: () => ctrl.pause(),
    seek: (s) => ctrl.seek(s),
    time: () => now,
    destroy: () => ctrl.destroy?.(),
  };
}

// odtwarzacz dla danego zrodla (null = zwykly plik, obsluga przez <audio>/<video>)
export function playerFor(m: Media) {
  if (m.source === "youtube") return youtube;
  if (m.source === "soundcloud") return soundcloud;
  if (m.source === "spotify") return spotify;
  return null;
}
