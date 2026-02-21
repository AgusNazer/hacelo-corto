"use client";

import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserClipItem, type UserVideoItem } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Clock3, Download, Search, Tag } from "lucide-react";
import { useEffect, useState } from "react";

const PAGE_SIZE = 12;
type LibraryView = "clips" | "videos";

type VisualStatus = "listo" | "revision" | "render";

const statusStyles: Record<VisualStatus, string> = {
  listo: "border-emerald-300/40 bg-emerald-300/10 text-emerald-200",
  revision: "border-amber-300/45 bg-amber-300/10 text-amber-100",
  render: "border-sky-300/45 bg-sky-300/10 text-sky-100"
};

function mapStatus(status: string): VisualStatus {
  const normalized = status.toLowerCase();
  if (normalized === "done" || normalized === "completed") {
    return "listo";
  }
  if (normalized === "failed" || normalized === "error") {
    return "revision";
  }
  return "render";
}

export default function LibraryPage() {
  const token = useAuthStore((state) => state.token);
  const [view, setView] = useState<LibraryView>("clips");
  const [clips, setClips] = useState<UserClipItem[]>([]);
  const [videos, setVideos] = useState<UserVideoItem[]>([]);
  const [totalClips, setTotalClips] = useState(0);
  const [totalVideos, setTotalVideos] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setError("No encontramos una sesion activa para traer la biblioteca.");
      return;
    }

    let cancelled = false;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        if (view === "clips") {
          const response = await videoApi.getMyClips(token, {
            limit: PAGE_SIZE,
            offset: (page - 1) * PAGE_SIZE,
            query
          });
          if (!cancelled) {
            setClips(response.clips);
            setTotalClips(response.total);
          }
        } else {
          const response = await videoApi.getMyVideos(token, {
            limit: PAGE_SIZE,
            offset: (page - 1) * PAGE_SIZE,
            query
          });
          if (!cancelled) {
            setVideos(response.videos);
            setTotalVideos(response.total);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "No pudimos cargar la biblioteca.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadData();

    return () => {
      cancelled = true;
    };
  }, [token, page, query, view]);

  const totalPages = Math.max(1, Math.ceil((view === "clips" ? totalClips : totalVideos) / PAGE_SIZE));

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <Panel className="relative overflow-hidden border-neon-cyan/25 bg-gradient-to-r from-night-900 via-night-800/85 to-night-900 p-5 sm:p-6">
        <div className="pointer-events-none absolute -right-14 -top-14 h-52 w-52 rounded-full bg-neon-cyan/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 left-1/4 h-44 w-44 rounded-full bg-neon-magenta/15 blur-3xl" />

        <div className="relative animate-fade-up">
          <p className="text-xs uppercase tracking-[0.25em] text-neon-cyan/80">biblioteca</p>
          <h1 className="mt-2 font-display text-2xl text-white sm:text-3xl">Tus clips y videos originales</h1>
          <p className="mt-2 max-w-2xl text-sm text-white/70">
            Cambia entre clips generados y videos subidos originales. La busqueda se hace en backend por nombre o ID.
          </p>
        </div>

        <div className="relative mt-4 inline-flex rounded-xl border border-white/12 bg-white/5 p-1 text-xs">
          <button
            type="button"
            className={[
              "rounded-lg px-3 py-1.5 transition",
              view === "clips" ? "bg-neon-cyan/20 text-neon-cyan" : "text-white/70 hover:text-white"
            ].join(" ")}
            onClick={() => {
              setView("clips");
              setPage(1);
            }}
          >
            Clips
          </button>
          <button
            type="button"
            className={[
              "rounded-lg px-3 py-1.5 transition",
              view === "videos" ? "bg-neon-cyan/20 text-neon-cyan" : "text-white/70 hover:text-white"
            ].join(" ")}
            onClick={() => {
              setView("videos");
              setPage(1);
            }}
          >
            Videos originales
          </button>
        </div>

        <div className="relative mt-5 grid gap-3 sm:grid-cols-1">
          <label className="group flex items-center gap-3 rounded-xl border border-white/12 bg-white/5 px-3 py-2 transition hover:border-neon-cyan/40">
            <Search size={15} className="text-neon-cyan/80" />
            <input
              placeholder={view === "clips" ? "Buscar por id de job o archivo fuente..." : "Buscar por id de video o archivo subido..."}
              className="w-full bg-transparent text-sm text-white/90 outline-none placeholder:text-white/40"
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
            />
          </label>
        </div>
      </Panel>

      {error ? (
        <Panel className="mt-5">
          <p className="rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>
        </Panel>
      ) : null}

      {isLoading ? (
        <Panel className="mt-5">
          <p className="text-sm text-white/70">Cargando clips de biblioteca...</p>
        </Panel>
      ) : null}

      {!isLoading && !error && view === "clips" && clips.length === 0 ? (
        <Panel className="mt-5">
          <p className="text-sm text-white/70">No encontramos clips para esa busqueda.</p>
        </Panel>
      ) : null}

      {!isLoading && !error && view === "videos" && videos.length === 0 ? (
        <Panel className="mt-5">
          <p className="text-sm text-white/70">No encontramos videos subidos para esa busqueda.</p>
        </Panel>
      ) : null}

      {view === "clips" ? (
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {clips.map((clip, index) => {
          const visualStatus = mapStatus(clip.status);

          return (
          <article
            key={clip.job_id}
            className="group animate-fade-up rounded-2xl border border-white/10 bg-gradient-to-b from-night-800/80 to-night-900/80 p-4 shadow-panel transition duration-300 hover:-translate-y-1 hover:border-neon-cyan/40"
            style={{ animationDelay: `${index * 90}ms` }}
          >
            <div className="relative mb-3 overflow-hidden rounded-xl border border-white/10 bg-night-900/80">
              {clip.output_path ? (
                <video controls preload="metadata" className="aspect-[9/13] w-full object-cover" src={clip.output_path} />
              ) : (
                <div className="aspect-[9/13] bg-[radial-gradient(circle_at_20%_20%,rgba(53,208,255,0.32),transparent_45%),radial-gradient(circle_at_80%_78%,rgba(255,79,216,0.28),transparent_50%),#0d1630]" />
              )}

              <span className={`absolute right-3 top-3 rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.2em] ${statusStyles[visualStatus]}`}>
                {visualStatus}
              </span>

              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs text-white/85">
                <span className="inline-flex items-center gap-1 rounded-full bg-black/35 px-2 py-1 backdrop-blur-sm">
                  <Clock3 size={12} />
                  clip
                </span>
                <span className="rounded-full bg-black/35 px-2 py-1 backdrop-blur-sm">9:16</span>
              </div>
            </div>

            <h2 className="font-display text-lg text-white">Job {clip.job_id.slice(0, 8)}</h2>

            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 rounded-full border border-neon-violet/35 bg-neon-violet/10 px-2 py-1 text-neon-violet">
                <Tag size={11} />
                Auto Reframe
              </span>
              <span className="rounded-full border border-white/15 bg-white/5 px-2 py-1 text-white/70">{clip.source_filename}</span>
            </div>

            <div className="mt-4 flex items-center gap-2">
              {clip.output_path ? (
                <a
                  href={clip.output_path}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-neon-cyan/40 bg-neon-cyan/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-neon-cyan transition hover:bg-neon-cyan/20"
                >
                  <Download size={13} />
                  Abrir clip
                </a>
              ) : (
                <span className="inline-flex flex-1 items-center justify-center rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/65">
                  Sin URL disponible
                </span>
              )}
            </div>
          </article>
          );
          })}
        </div>
      ) : (
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {videos.map((video, index) => (
            <article
              key={video.video_id}
              className="group animate-fade-up rounded-2xl border border-white/10 bg-gradient-to-b from-night-800/80 to-night-900/80 p-4 shadow-panel transition duration-300 hover:-translate-y-1 hover:border-neon-cyan/40"
              style={{ animationDelay: `${index * 90}ms` }}
            >
              <div className="relative mb-3 overflow-hidden rounded-xl border border-white/10 bg-night-900/80">
                {video.preview_url ? (
                  <video controls preload="metadata" className="aspect-[16/9] w-full object-cover" src={video.preview_url} />
                ) : (
                  <div className="aspect-[16/9] grid place-items-center bg-[radial-gradient(circle_at_20%_20%,rgba(53,208,255,0.22),transparent_45%),#0d1630] text-xs text-white/65">
                    Sin preview disponible
                  </div>
                )}
              </div>

              <h2 className="font-display text-lg text-white">Video {video.video_id.slice(0, 8)}</h2>
              <p className="mt-2 rounded-full border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/70">{video.filename}</p>
              <p className="mt-2 inline-flex rounded-full border border-neon-cyan/35 bg-neon-cyan/10 px-2 py-1 text-xs text-neon-cyan">
                Estado: {video.status ?? "uploaded"}
              </p>

              <div className="mt-4 flex items-center gap-2">
                {video.preview_url ? (
                  <a
                    href={video.preview_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-neon-cyan/40 bg-neon-cyan/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-neon-cyan transition hover:bg-neon-cyan/20"
                  >
                    <Download size={13} />
                    Abrir video
                  </a>
                ) : (
                  <span className="inline-flex flex-1 items-center justify-center rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/65">
                    Sin URL disponible
                  </span>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {totalPages > 1 ? (
        <Panel className="mt-5">
          <div className="flex items-center justify-between text-sm text-white/80">
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
        </Panel>
      ) : null}
    </section>
  );
}
