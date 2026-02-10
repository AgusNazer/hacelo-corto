import { useAppStore } from "../store/useAppStore";

export function LandingPage() {
  const clicks = useAppStore((state) => state.clicks);
  const increaseClicks = useAppStore((state) => state.increaseClicks);

  return (
    <section className="mx-auto flex min-h-screen w-full max-w-4xl flex-col items-center justify-center gap-8 px-6 py-12">
      <p className="rounded-full border border-brand-500/30 bg-brand-100 px-4 py-1 text-sm font-medium text-brand-700">
        Frontend workspace
      </p>

      <h1 className="text-center text-4xl font-bold tracking-tight sm:text-5xl">
        Landing inicial del equipo Frontend
      </h1>

      <p className="max-w-2xl text-center text-lg text-slate-600">
        React Router ya esta configurado para escalar en rutas por feature. Desde
        aca podemos construir las vistas de producto sin tocar backend.
      </p>

      <button
        type="button"
        className="rounded-lg bg-brand-500 px-5 py-3 text-white transition hover:bg-brand-700"
        onClick={increaseClicks}
      >
        Clicks del equipo: {clicks}
      </button>
    </section>
  );
}
