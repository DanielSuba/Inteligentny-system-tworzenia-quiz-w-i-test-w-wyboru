/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, expect, it, vi } from "vitest";
import type { Media } from "@/api/media";
import { playerFor } from "@/components/media/players";

// atrapa kontrolera Spotify: zapisuje komendy, zdarzenia wysylamy recznie
function fakeSpotify() {
  const listeners: Record<string, (e: any) => void> = {};
  const ctrl = {
    resume: vi.fn(),
    pause: vi.fn(),
    togglePlay: vi.fn(),
    seek: vi.fn(),
    destroy: vi.fn(),
    addListener: (name: string, fn: (e: any) => void) => (listeners[name] = fn),
  };
  const api = { createController: (_el: any, _opt: any, ok: (c: any) => void) => ok(ctrl) };
  return { ctrl, api, emit: (data: any) => listeners.playback_update({ data }) };
}

describe("odtwarzacz Spotify", () => {
  it("steruje przez resume/pause i czyta pozycje", async () => {
    const { ctrl, api, emit } = fakeSpotify();
    const media = { source: "spotify", embedId: "track/abc" } as Media;
    const onState = vi.fn();
    const create = playerFor(media)!;
    const pending = create(media, document.createElement("div"), onState);
    (window as any).onSpotifyIframeApiReady(api);
    const c = await pending;

    c.seek(5);
    c.play();
    expect(ctrl.seek).toHaveBeenCalledWith(5);
    expect(ctrl.resume).toHaveBeenCalled();
    expect(ctrl.togglePlay).not.toHaveBeenCalled();

    emit({ isPaused: false, position: 12000 });
    expect(onState).toHaveBeenLastCalledWith({ playing: true, time: 12 });
    expect(c.time()).toBe(12);

    // pauza nigdy nie wlacza muzyki, nawet gdy stan jest nieznany
    c.pause();
    c.pause();
    expect(ctrl.pause).toHaveBeenCalledTimes(2);
    expect(ctrl.resume).toHaveBeenCalledTimes(1);
  });
});
