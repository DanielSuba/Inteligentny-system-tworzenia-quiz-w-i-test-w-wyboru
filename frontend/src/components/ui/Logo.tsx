import { PixelIcon } from "@/components/ui/PixelIcon";

// logo: pikselowe kowadlo i nazwa fontem ForgePixel
export function Logo() {
  return (
    <span className="flex items-center gap-2.5 text-acc">
      <PixelIcon name="anvil" scale={2} />
      <span className="font-pixel text-[24px] leading-none text-fg">QuizForge</span>
    </span>
  );
}
