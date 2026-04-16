import { cva } from "class-variance-authority";

export const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-gray-900 text-white",
        secondary: "border-transparent bg-gray-100 text-gray-900",
        success: "border-transparent bg-green-100 text-green-800",
        destructive: "border-transparent bg-red-100 text-red-800",
        warning: "border-transparent bg-yellow-100 text-yellow-800",
        outline: "text-gray-900",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);
