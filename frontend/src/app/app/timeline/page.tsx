"use client";

import { VideoSettings } from "@/src/components/home/VideoSettings";
import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserClipItem, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 10;

function normalizeClipStatus(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "done" || normalized === "completed") {
    return "listo";
  }
  if (normalized === "failed" || normalized === "error") {
    return "error";
  }
  return "render";
}

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

export default function TimelinePage() {
  const token = useAuthStore((state) => state.token);
  const [clips, setClips] = useState<UserClipItem[]>([]);
  const [totalClips, setTotalClips] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setError("No encontramos una sesion activa para cargar el timeline.");
      return;
    }

    let cancelled = false;

    const loadClips = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await videoApi.getMyClips(token, {
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
          query
        });
        if (cancelled) {
          return;
        }

        setClips(response.clips);
        setTotalClips(response.total);
        setSelectedClipId(response.clips[0]?.job_id ?? null);
      } catch (loadError) {
        if (!cancelled) {
          setError(normalizeVideoError(loadError, "No pudimos cargar tus clips."));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadClips();

    return () => {
      cancelled = true;
    };
  }, [token, page, query]);

  const totalPages = Math.max(1, Math.ceil(totalClips / PAGE_SIZE));

  const selectedClip = useMemo(
    () => clips.find((clip) => clip.job_id === selectedClipId) ?? null,
    [clips, selectedClipId]
  );

  const selectedPreviewUrl = selectedClip?.output_path ?? null;

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">timeline</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Preview y recorte</h3>
          <label className="mt-3 flex items-center gap-2 rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-white/80 transition hover:border-neon-cyan/40">
            <Search size={14} className="text-neon-cyan/80" />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
              placeholder="Buscar clip por job o archivo..."
              className="w-full bg-transparent text-sm text-white/90 outline-none placeholder:text-white/40"
            />
          </label>

          {isLoading ? (
            <p className="mt-4 text-sm text-white/70">Cargando clips...</p>
          ) : error ? (
            <p className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>
          ) : selectedPreviewUrl ? (
            <VideoPreview
              videoPreviewUrl={selectedPreviewUrl}
              onTrimChange={(start, end) => {
                console.log("Ajuste de recorte en timeline:", { start, end });
              }}
            />
          ) : (
            <p className="mt-4 text-sm text-white/70">
              Este clip todavia no tiene salida lista para preview. Proba otro clip o espera a que termine el render.
            </p>
          )}

          {!isLoading && clips.length > 0 ? (
            <>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {clips.map((clip) => {
                  const normalized = normalizeClipStatus(clip.status);
                  return (
                    <button
                      type="button"
                      key={clip.job_id}
                      onClick={() => setSelectedClipId(clip.job_id)}
                      className={[
                        "rounded-xl border px-3 py-2 text-left text-sm transition",
                        selectedClipId === clip.job_id
                          ? "border-neon-cyan/45 bg-neon-cyan/10 text-white"
                          : "border-white/10 bg-white/5 text-white/75 hover:border-white/20 hover:text-white"
                      ].join(" ")}
                    >
                      <p className="font-semibold">Clip {clip.job_id.slice(0, 8)}</p>
                      <p className="mt-1 text-xs text-white/60">Fuente: {clip.source_filename}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.16em] text-neon-cyan/80">Estado: {normalized}</p>
                    </button>
                  );
                })}
              </div>

              {totalPages > 1 ? (
                <div className="mt-4 flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80">
                  <span>Pagina {page} de {totalPages}</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-white/15 px-3 py-1.5 text-xs transition hover:border-white/35 disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={page <= 1 || isLoading}
                      onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                    >
                      Anterior
                    </button>
                    <button
                      type="button"
                      className="rounded-lg border border-white/15 px-3 py-1.5 text-xs transition hover:border-white/35 disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={page >= totalPages || isLoading}
                      onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                    >
                      Siguiente
                    </button>
                  </div>
                </div>
              ) : null}
            </>
          ) : null}
        </Panel>

        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">configuracion</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Ajustes de recorte</h3>
          <VideoSettings />
        </Panel>
      </div>
    </section>
  );
}
