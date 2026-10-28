import { api } from "@/api/client";

export type MediaKind = "image" | "audio" | "video";
export type Crop = { x: number; y: number; w: number; h: number };

export type Media = {
  id: string;
  kind: MediaKind;
  source: "link" | "upload" | "youtube" | "soundcloud" | "spotify";
  url: string;
  youtubeId: string | null;
  embedId: string | null;
  startS: number | null;
  endS: number | null;
  mime: string | null;
  crop: Crop | null;
  displayWidth: number | null;
  hideVideo: boolean;
};

export type MediaLinkIn = { kind: MediaKind; url: string; startS?: number; endS?: number };
export type MediaUpdate = Partial<{
  startS: number | null;
  endS: number | null;
  crop: Crop | null;
  displayWidth: number;
  hideVideo: boolean;
}>;

export const linkMedia = (data: MediaLinkIn) => api<Media>("/media-items/link", { json: data });

export function uploadMedia(file: File, kind: MediaKind) {
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file);
  return api<Media>("/media-items/upload", { form });
}

export const updateMedia = (id: string, data: MediaUpdate) =>
  api<Media>(`/media-items/${id}`, { method: "PATCH", json: data });
