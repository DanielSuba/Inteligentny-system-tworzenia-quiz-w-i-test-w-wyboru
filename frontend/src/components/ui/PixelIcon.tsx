import { icons, type IconName } from "@/components/ui/pixelIcons";

type Props = { name: IconName; scale?: number; className?: string };

// rysuje ikone jako SVG z kwadracikow
export function PixelIcon({ name, scale = 2, className }: Props) {
  const rows = icons[name];
  const w = Math.max(...rows.map((r) => r.length));
  const h = rows.length;
  const rects = [];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < rows[y].length; x++) {
      if (rows[y][x] === "#")
        rects.push(<rect key={`${x}-${y}`} x={x} y={y} width={1} height={1} />);
    }
  }
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      width={w * scale}
      height={h * scale}
      fill="currentColor"
      shapeRendering="crispEdges"
      aria-hidden="true"
      className={className}
    >
      {rects}
    </svg>
  );
}
