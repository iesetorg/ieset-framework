import { type ReactNode } from "react";

type Variant = "accent" | "green" | "amber" | "red" | "muted";

const variantClasses: Record<Variant, string> = {
  accent: "bg-accent-soft text-accent",
  green: "bg-green-soft text-green",
  amber: "bg-amber-soft text-amber",
  red: "bg-red-soft text-red",
  muted: "bg-code-bg text-muted",
};

export function Badge({
  variant = "accent",
  dot = false,
  children,
  className,
}: {
  variant?: Variant;
  dot?: boolean;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={
        "inline-flex items-center rounded-sm px-2.5 py-[3px] text-xs font-medium " +
        variantClasses[variant] +
        (className ? " " + className : "")
      }
    >
      {dot && <span className="mr-1.5 h-[6px] w-[6px] rounded-full bg-current" />}
      {children}
    </span>
  );
}
