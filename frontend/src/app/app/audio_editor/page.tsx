"use client";

import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserAudioItem, type UserClipItem, type UserVideoItem, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Music2, Search } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 10;

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

function isTerminalStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed" || normalized === "failed" || normalized === "error";
}

function isDoneStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed";
}

function toTimeLabel(seconds: number) {
  const min = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const sec = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${min}:${sec}`;
}

export default function AudioEditorPage() {
  const searchParams = useSearchParams();
  const preferredVideoId = searchParams.get("videoId")?.trim() ?? "";
  const preferredClipId = searchParams.get("clipId")?.trim() ?? "";
  const token = useAuthStore((state) => state.token);

  const [videos, setVideos] = useState<UserVideoItem[]>([]);
  const [totalVideos, setTotalVideos] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [isLoadingVideos, setIsLoadingVideos] = useState(true);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [focusedClip, setFocusedClip] = useState<UserClipItem | null>(null);

  const [audios, setAudios] = useState<UserAudioItem[]>([]);
  const [isLoadingAudios, setIsLoadingAudios] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [selectedAudioId, setSelectedAudioId] = useState<string | null>(null);
  const [selectedAudioUrl, setSelectedAudioUrl] = useState<string | null>(null);

  const [audioOffsetSec, setAudioOffsetSec] = useState(0);
  const [audioStartSec, setAudioStartSec] = useState(0);
  const [audioEndSec, setAudioEndSec] = useState(15);
  const [audioVolume, setAudioVolume] = useState(1);

  const [isSubmittingAudio, setIsSubmittingAudio] = useState(false);
  const [audioSubmitInfo, setAudioSubmitInfo] = useState<string | null>(null);
  const [audioSubmitError, setAudioSubmitError] = useState<string | null>(null);
  const [audioJobId, setAudioJobId] = useState<string | null>(null);
  const [isPollingAudioJob, setIsPollingAudioJob] = useState(false);
  const [mixedVideoUrl, setMixedVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoadingVideos(false);
      setVideoError("No encontramos una sesion activa para cargar videos.");
      return;
    }

    let cancelled = false;

    const loadVideos = async () => {
      setIsLoadingVideos(true);
      setVideoError(null);
      try {
        let selectedClip: UserClipItem | null = null;
        let preferredVideoFromQuery = preferredVideoId;

        if (preferredClipId) {
          try {
            const clipResponse = await videoApi.getMyClipById(preferredClipId, token);
            selectedClip = clipResponse.clip;
            if (selectedClip && !preferredVideoFromQuery) {
              preferredVideoFromQuery = selectedClip.video_id;
            }
          } catch {
            selectedClip = null;
          }
        }

        const response = await videoApi.getMyVideos(token, {
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
          query
        });

        if (cancelled) {
          return;
        }

        let nextVideos = response.videos;
        if (preferredVideoFromQuery && !response.videos.some((video) => video.video_id === preferredVideoFromQuery)) {
          try {
            const preferredVideo = await videoApi.getMyVideoById(preferredVideoFromQuery, token);
            nextVideos = [
              {
                video_id: preferredVideo.video_id,
                filename: preferredVideo.filename,
                status: preferredVideo.status,
                uploaded_at: preferredVideo.uploaded_at,
                preview_url: preferredVideo.preview_url
              },
              ...response.videos.filter((video) => video.video_id !== preferredVideo.video_id)
            ];
          } catch {
            nextVideos = response.videos;
          }
        }

        setVideos(nextVideos);
        setFocusedClip(selectedClip);
        setTotalVideos(response.total);
        setSelectedVideoId((prev) => {
          if (preferredVideoFromQuery && nextVideos.some((video) => video.video_id === preferredVideoFromQuery)) {
            return preferredVideoFromQuery;
          }
          if (prev && nextVideos.some((video) => video.video_id === prev)) {
            return prev;
          }
          return nextVideos[0]?.video_id ?? null;
        });
      } catch (loadError) {
        if (!cancelled) {
          setVideoError(normalizeVideoError(loadError, "No pudimos cargar tus videos."));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingVideos(false);
        }
      }
    };

    void loadVideos();

    return () => {
      cancelled = true;
    };
  }, [token, page, preferredClipId, preferredVideoId, query]);

  useEffect(() => {
    if (!token) {
      setAudios([]);
      return;
    }

    let cancelled = false;

    const loadAudios = async () => {
      setIsLoadingAudios(true);
      setAudioError(null);
      try {
        const response = await videoApi.getMyAudios(token, { limit: 50, offset: 0 });
        if (cancelled) {
          return;
        }

        setAudios(response.audios);
        setSelectedAudioId((prev) => {
          if (prev && response.audios.some((audio) => audio.audio_id === prev)) {
            return prev;
          }
          return response.audios[0]?.audio_id ?? null;
        });
      } catch (loadError) {
        if (!cancelled) {
          setAudioError(normalizeVideoError(loadError, "No pudimos cargar tus audios."));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingAudios(false);
        }
      }
    };

    void loadAudios();

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!token || !selectedAudioId) {
      setSelectedAudioUrl(null);
      return;
    }

    let cancelled = false;

    const resolveAudioUrl = async () => {
      try {
        const response = await videoApi.getAudioUrl(selectedAudioId, token);
        if (!cancelled) {
          setSelectedAudioUrl(response.url);
        }
      } catch {
        if (!cancelled) {
          setSelectedAudioUrl(null);
        }
      }
    };

    void resolveAudioUrl();

    return () => {
      cancelled = true;
    };
  }, [selectedAudioId, token]);

  useEffect(() => {
    if (!token || !audioJobId) {
      setIsPollingAudioJob(false);
      return;
    }

    let cancelled = false;

    const syncAudioJob = async () => {
      try {
        const status = await videoApi.getJobStatus(audioJobId, token);
        if (cancelled) {
          return;
        }

        if (status.output_path) {
          setMixedVideoUrl(status.output_path);
        }

        if (isDoneStatus(status.status)) {
          setAudioSubmitInfo(`Mezcla de audio lista. Job ${audioJobId.slice(0, 8)} finalizado.`);
        }

        if (isTerminalStatus(status.status) && (status.output_path || !isDoneStatus(status.status))) {
          window.clearInterval(intervalId);
          setIsPollingAudioJob(false);

          if (!isDoneStatus(status.status)) {
            setAudioSubmitError(`La mezcla termino con estado ${status.status}.`);
          }
        }
      } catch {
        if (!cancelled) {
          setAudioSubmitError("No pudimos actualizar el estado del job de mezcla.");
        }
      }
    };

    setIsPollingAudioJob(true);
    const intervalId = window.setInterval(() => {
      void syncAudioJob();
    }, 4000);

    void syncAudioJob();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsPollingAudioJob(false);
    };
  }, [audioJobId, token]);

  const totalPages = Math.max(1, Math.ceil(totalVideos / PAGE_SIZE));
  const selectedVideo = useMemo(() => videos.find((video) => video.video_id === selectedVideoId) ?? null, [videos, selectedVideoId]);
  const previewUrl = mixedVideoUrl ?? focusedClip?.output_path ?? selectedVideo?.preview_url ?? null;

  const handleAddAudioToVideo = async () => {
    if (!token || !selectedVideoId || !selectedAudioId) {
      setAudioSubmitError("Selecciona video y audio para iniciar la mezcla.");
      return;
    }

    if (audioEndSec <= audioStartSec) {
      setAudioSubmitError("El fin del segmento de audio debe ser mayor al inicio.");
      return;
    }

    setIsSubmittingAudio(true);
    setAudioSubmitError(null);
    setAudioSubmitInfo(null);
    setMixedVideoUrl(null);

    try {
      const response = await videoApi.addAudioToVideo(selectedVideoId, token, {
        audio_id: selectedAudioId,
        audio_offset_sec: Math.max(0, Math.floor(audioOffsetSec)),
        audio_start_sec: Math.max(0, Math.floor(audioStartSec)),
        audio_end_sec: Math.max(1, Math.ceil(audioEndSec)),
        audio_volume: Math.min(2, Math.max(0.1, Number(audioVolume.toFixed(2))))
      });

      setAudioJobId(response.job_id);
      setAudioSubmitInfo(`Mezcla enviada a cola. Job ${response.job_id.slice(0, 8)} en estado ${response.status}.`);
    } catch (mixError) {
      setAudioSubmitError(normalizeVideoError(mixError, "No pudimos enviar el job para mezclar audio."));
    } finally {
      setIsSubmittingAudio(false);
    }
  };

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">audio editor</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Video + pista de audio</h3>

          <label className="mt-3 flex items-center gap-2 rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-white/80 transition hover:border-neon-violet/40">
            <Search size={14} className="text-neon-violet/80" />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
              placeholder="Buscar video por id o archivo..."
              className="w-full bg-transparent text-sm text-white/90 outline-none placeholder:text-white/40"
            />
          </label>

          {isLoadingVideos ? (
            <p className="mt-4 text-sm text-white/70">Cargando videos...</p>
          ) : videoError ? (
            <p className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{videoError}</p>
          ) : previewUrl ? (
            <VideoPreview videoPreviewUrl={previewUrl} onTrimChange={() => {}} />
          ) : (
            <p className="mt-4 text-sm text-white/70">Selecciona un video con preview disponible.</p>
          )}

          <div className="mt-4 rounded-xl border border-neon-violet/30 bg-neon-violet/5 p-3">
            <p className="text-xs uppercase tracking-[0.16em] text-neon-violet/85">Pistas</p>
            <div className="mt-2 grid gap-2">
              <div className="rounded-lg border border-white/10 bg-night-900/80 p-2">
                <p className="text-[11px] text-white/65">Track video</p>
                <div className="mt-2 h-6 rounded bg-gradient-to-r from-sky-400/25 to-sky-300/60" />
              </div>
              <div className="rounded-lg border border-white/10 bg-night-900/80 p-2">
                <div className="flex items-center justify-between text-[11px] text-white/65">
                  <span>Track audio</span>
                  <span>
                    {toTimeLabel(audioStartSec)} - {toTimeLabel(audioEndSec)}
                  </span>
                </div>
                <div className="mt-2 h-6 overflow-hidden rounded bg-night-950/90">
                  <div
                    className="h-full rounded bg-gradient-to-r from-neon-violet/65 to-neon-magenta/75"
                    style={{
                      marginLeft: `${Math.min(audioOffsetSec * 2, 80)}px`,
                      width: `${Math.max((audioEndSec - audioStartSec) * 5, 24)}px`
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {videos.map((video) => (
              <button
                type="button"
                key={video.video_id}
                onClick={() => {
                  setSelectedVideoId(video.video_id);
                  setMixedVideoUrl(null);
                }}
                className={[
                  "rounded-xl border px-3 py-2 text-left text-sm transition",
                  selectedVideoId === video.video_id
                    ? "border-neon-violet/45 bg-neon-violet/10 text-white"
                    : "border-white/10 bg-white/5 text-white/75 hover:border-white/20 hover:text-white"
                ].join(" ")}
              >
                <p className="font-semibold">Video {video.video_id.slice(0, 8)}</p>
                <p className="mt-1 text-xs text-white/60">Archivo: {video.filename}</p>
              </button>
            ))}
          </div>

          {totalPages > 1 ? (
            <div className="mt-4 flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80">
              <span>Pagina {page} de {totalPages}</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs transition hover:border-white/35 disabled:opacity-40"
                  disabled={page <= 1 || isLoadingVideos}
                  onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                >
                  Anterior
                </button>
                <button
                  type="button"
                  className="rounded-lg border border-white/15 px-3 py-1.5 text-xs transition hover:border-white/35 disabled:opacity-40"
                  disabled={page >= totalPages || isLoadingVideos}
                  onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                >
                  Siguiente
                </button>
              </div>
            </div>
          ) : null}
        </Panel>

        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">mezcla</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Ajustes de audio</h3>

          {isLoadingAudios ? <p className="mt-3 text-sm text-white/70">Cargando audios...</p> : null}
          {audioError ? <p className="mt-3 text-sm text-rose-200">{audioError}</p> : null}

          {!isLoadingAudios && audios.length > 0 ? (
            <>
              <label className="mt-3 block text-xs text-white/75">
                Audio de biblioteca
                <select
                  value={selectedAudioId ?? ""}
                  onChange={(event) => setSelectedAudioId(event.target.value || null)}
                  className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                >
                  {audios.map((audio) => (
                    <option key={audio.audio_id} value={audio.audio_id}>
                      {audio.filename}
                    </option>
                  ))}
                </select>
              </label>

              {selectedAudioUrl ? (
                <audio controls preload="metadata" className="mt-3 w-full rounded-lg [accent-color:#cba6f7]" src={selectedAudioUrl} />
              ) : null}

              <div className="mt-3 rounded-xl border border-white/12 bg-white/5 p-3 text-xs text-white/80">
                <p className="text-neon-violet">Referencia rapida</p>
                <p className="mt-1">- `offset en video`: segundo del video donde empieza a sonar el audio.</p>
                <p>- `inicio audio`: desde que segundo del archivo de audio recortas.</p>
                <p>- `fin audio`: hasta que segundo del archivo de audio usas.</p>
                <p>- `volumen`: ganancia del audio agregado (1.0 = normal).</p>
              </div>

              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <label className="text-xs text-white/75">
                  Offset en video (seg)
                  <input
                    type="number"
                    min={0}
                    value={audioOffsetSec}
                    onChange={(event) => setAudioOffsetSec(Number(event.target.value || 0))}
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
                <label className="text-xs text-white/75">
                  Volumen (0.1 - 2.0)
                  <input
                    type="number"
                    min={0.1}
                    max={2}
                    step={0.1}
                    value={audioVolume}
                    onChange={(event) => setAudioVolume(Number(event.target.value || 1))}
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
                <label className="text-xs text-white/75">
                  Inicio audio (seg)
                  <input
                    type="number"
                    min={0}
                    value={audioStartSec}
                    onChange={(event) => setAudioStartSec(Number(event.target.value || 0))}
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
                <label className="text-xs text-white/75">
                  Fin audio (seg)
                  <input
                    type="number"
                    min={1}
                    value={audioEndSec}
                    onChange={(event) => setAudioEndSec(Number(event.target.value || 1))}
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
              </div>

              <button
                type="button"
                onClick={() => void handleAddAudioToVideo()}
                disabled={!selectedVideoId || !selectedAudioId || isSubmittingAudio}
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-neon-violet/45 bg-neon-violet/15 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-neon-violet transition hover:bg-neon-violet/20 disabled:opacity-40"
              >
                <Music2 size={14} /> {isSubmittingAudio ? "Encolando..." : "Aplicar audio al video"}
              </button>

              {audioSubmitInfo ? <p className="mt-2 text-xs text-neon-mint">{audioSubmitInfo}</p> : null}
              {audioSubmitError ? <p className="mt-2 text-xs text-rose-200">{audioSubmitError}</p> : null}
              {isPollingAudioJob ? <p className="mt-2 text-xs text-white/65">Procesando mezcla de audio...</p> : null}
            </>
          ) : null}

          {!isLoadingAudios && audios.length === 0 ? (
            <p className="mt-3 text-sm text-white/70">No hay audios cargados. Subi uno desde Home para mezclarlo aca.</p>
          ) : null}
        </Panel>
      </div>
    </section>
  );
}
