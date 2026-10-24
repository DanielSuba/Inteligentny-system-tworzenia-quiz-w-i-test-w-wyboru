import { api } from "@/api/client";

export type MediaKind = "image" | "audio" | "video";

export type Media = {
  id: string;
  kind: MediaKind;
  source: "link" | "upload" | "youtube";
  url: string;
  youtubeId: string | null;
  startS: number | null;
  endS: number | null;
  mime: string | null;
};

export type MediaLinkIn = { kind: MediaKind; url: string; startS?: number; endS?: number };

export const linkMedia = (data: MediaLinkIn) => api<Media>("/media-items/link", { json: data });

export function uploadMedia(file: File, kind: MediaKind) {
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file);
  return api<Media>("/media-items/upload", { form });
}
