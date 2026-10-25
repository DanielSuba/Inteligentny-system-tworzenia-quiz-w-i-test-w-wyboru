import { PixelIcon } from "@/components/ui/PixelIcon";

// logo: pikselowy zwoj manuskryptu i nazwa fontem ForgePixel
export function Logo() {
  return (
    <span className="flex items-center gap-2.5 text-acc">
      <PixelIcon name="scroll" scale={2} />
      <span className="font-pixel text-[24px] leading-none text-fg">Apocrypha</span>
    </span>
  );
}
