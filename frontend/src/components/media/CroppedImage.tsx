import { useState } from "react";
import type { Media } from "@/api/media";

// obraz z zapisanym kadrem: oryginal zostaje bez zmian, kadr to tylko "okno" na fragment obrazu
export function CroppedImage({ media }: { media: Media }) {
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);
  const crop = media.crop;
  const width = `${media.displayWidth ?? 100}%`;

  if (!crop) {
    return (
      <img
        src={media.url}
        alt=""
        style={{ width, maxWidth: "100%" }}
        className="max-h-[28rem] border border-line object-contain shadow-ring"
      />
    );
  }

  // proporcje kadru z rozmiaru oryginalu (znanego po wczytaniu obrazu)
  const ratio = size ? (crop.w * size.w) / (crop.h * size.h) : crop.w / crop.h;
  return (
    <div
      className="relative max-w-full overflow-hidden border border-line shadow-ring"
      style={{ width, aspectRatio: String(ratio) }}
    >
      <img
        src={media.url}
        alt=""
        onLoad={(e) =>
          setSize({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })
        }
        className="absolute max-w-none"
        style={{
          width: `${10000 / crop.w}%`,
          height: `${10000 / crop.h}%`,
          left: `${(-crop.x * 100) / crop.w}%`,
          top: `${(-crop.y * 100) / crop.h}%`,
        }}
      />
    </div>
  );
}
