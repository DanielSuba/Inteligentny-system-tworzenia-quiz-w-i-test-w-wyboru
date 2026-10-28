import { useState } from "react";
import Cropper, { type Area } from "react-easy-crop";
import { useTranslation } from "react-i18next";
import type { Crop } from "@/api/media";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const aspects = [
  { key: "16:9", v: 16 / 9 },
  { key: "4:3", v: 4 / 3 },
  { key: "1:1", v: 1 },
  { key: "3:4", v: 3 / 4 },
];

type Props = { url: string; onSave: (crop: Crop | null) => void; onCancel: () => void };

// wybor kadru: przeciaganie i powiekszanie; zapisywany jest tylko prostokat w % oryginalu
export function CropEditor({ url, onSave, onCancel }: Props) {
  const { t } = useTranslation("quiz");
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [aspect, setAspect] = useState(aspects[0].v);
  const [area, setArea] = useState<Area | null>(null);

  return (
    <div className="flex flex-col gap-3 border border-line bg-surf p-3">
      <div className="relative h-72 w-full bg-bg">
        <Cropper
          image={url}
          crop={pos}
          zoom={zoom}
          aspect={aspect}
          onCropChange={setPos}
          onZoomChange={setZoom}
          onCropComplete={(percent) => setArea(percent)}
        />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {aspects.map((a) => (
          <button
            key={a.key}
            aria-pressed={aspect === a.v}
            onClick={() => setAspect(a.v)}
            className={cn(
              "border px-2 py-1 text-sm",
              aspect === a.v ? "border-acc text-acc" : "border-line text-mut",
            )}
          >
            {a.key}
          </button>
        ))}
        <label className="ml-auto flex items-center gap-2 text-sm text-mut">
          {t("media.zoom")}
          <input
            type="range"
            min={1}
            max={4}
            step={0.05}
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="accent-[var(--acc)]"
          />
        </label>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button
          disabled={!area}
          onClick={() => area && onSave({ x: area.x, y: area.y, w: area.width, h: area.height })}
        >
          {t("media.saveCrop")}
        </Button>
        <Button variant="secondary" onClick={() => onSave(null)}>
          {t("media.noCrop")}
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          {t("media.cancel")}
        </Button>
      </div>
    </div>
  );
}
