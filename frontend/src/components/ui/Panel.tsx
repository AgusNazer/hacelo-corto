import { HTMLAttributes } from "react";

type PanelVariant = "default" | "accent";

type PanelProps = HTMLAttributes<HTMLDivElement> & {
  variant?: PanelVariant;
};

const variantStyles: Record<PanelVariant, string> = {
  default: "border-white/10 bg-night-800/55",
  accent: "border-neon-cyan/30 bg-gradient-to-b from-night-800/80 to-night-900/70"
};

export function Panel({ className, variant = "default", ...props }: PanelProps) {
  const classes = ["rounded-2xl border p-5 shadow-panel", variantStyles[variant], className]
    .filter(Boolean)
    .join(" ");

  return <div className={classes} {...props} />;
}
