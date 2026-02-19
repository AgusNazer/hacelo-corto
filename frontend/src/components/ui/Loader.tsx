import { LoaderCircle } from "lucide-react";

type LoaderProps = {
  label?: string;
  className?: string;
};

export function Loader({ label = "Cargando...", className }: LoaderProps) {
  const classes = ["inline-flex items-center gap-2 text-sm text-white/75", className].filter(Boolean).join(" ");

  return (
    <div className={classes} role="status" aria-live="polite">
      <LoaderCircle size={16} className="animate-spin text-neon-cyan" />
      <span>{label}</span>
    </div>
  );
}
