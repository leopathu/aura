/**
 * Utility for merging Tailwind CSS class names.
 * Combines clsx for conditional logic and tailwind-merge to resolve conflicts.
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
