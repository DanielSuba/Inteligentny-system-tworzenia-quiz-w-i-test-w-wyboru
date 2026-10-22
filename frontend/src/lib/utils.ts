import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// laczy klasy Tailwinda bez konfliktow (jak w shadcn/ui)
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
