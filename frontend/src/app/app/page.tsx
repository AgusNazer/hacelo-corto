"use client";

import { GeneratedClipsSection, type Clip } from "@/src/components/home/GeneratedClipsSection";
import { ProjectStatusPanel } from "@/src/components/home/ProjectStatusPanel";
import { UploadDropzone } from "@/src/components/home/UploadDropzone";
import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { VideoSettings } from "@/src/components/home/VideoSettings";
import { Panel } from "@/src/components/ui/Panel";
import { VideoApiError, type AutoReframeJobItem, type VideoUploadResponse, videoApi } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useEffect, useMemo, useState } from "react";

function toTimeLabel(seconds: number) {
  const min = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const sec = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${min}:${sec}`;
}

function mapJobStatusToClipStatus(status: string): Clip["status"] {
  const normalized = status.toLowerCase();
  if (normalized === "completed") {
    return "listo";
  }

  if (normalized === "failed") {
    return "revision";
  }

  return "render";
}

function mapJobsToClips(jobs: AutoReframeJobItem[]): Clip[] {
  return jobs.map((job, index) => ({
    id: job.job_id,
    title: `Clip ${index + 1}`,
    duration: toTimeLabel(Math.max(job.end_sec - job.start_sec, 0)),
    preset: "Auto Reframe",
    status: mapJobStatusToClipStatus(job.status)
  }));
}

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    if (error.status === 400) {
      return "El archivo de video es invalido o no cumple los requisitos.";
    }

    if (error.status === 401) {
      return "Tu sesion expiro. Vuelve a iniciar sesion para continuar.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    const normalizedMessage = error.message.toLowerCase();
    if (normalizedMessage.includes("failed to fetch") || normalizedMessage.includes("networkerror")) {
      return "No pudimos conectar con el servidor. Intenta de nuevo en unos segundos.";
    }

    return error.message;
  }

  return fallbackMessage;
}

export default function AppHomePage() {
  const token = useAuthStore((state) => state.token);
  const [isUploading, setIsUploading] = useState(false);
  const [isCreatingJobs, setIsCreatingJobs] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResponse | null>(null);
  const [autoJobCount, setAutoJobCount] = useState(0);
  const [createdJobs, setCreatedJobs] = useState<AutoReframeJobItem[]>([]);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);

  const hasVideo = Boolean(uploadedVideo);
  const visibleClips = useMemo(() => mapJobsToClips(createdJobs), [createdJobs]);

  useEffect(() => {
    return () => {
      if (videoPreviewUrl) {
        URL.revokeObjectURL(videoPreviewUrl);
      }
    };
  }, [videoPreviewUrl]);

  const handleUpload = async (file: File) => {
    const localPreviewUrl = URL.createObjectURL(file);

    setIsUploading(true);
    setIsCreatingJobs(false);
    setUploadedVideo(null);
    setCreatedJobs([]);
    setAutoJobCount(0);
    setUploadError(null);
    setJobError(null);

    let uploaded: VideoUploadResponse;

    try {
      uploaded = await videoApi.upload(file, token);
    } catch (error) {
      URL.revokeObjectURL(localPreviewUrl);
      setVideoPreviewUrl(null);
      setUploadError(normalizeVideoError(error, "No pudimos subir el video."));
      setIsUploading(false);
      return;
    }

    setUploadedVideo(uploaded);
    setVideoPreviewUrl((prev) => {
      if (prev) {
        URL.revokeObjectURL(prev);
      }
      return localPreviewUrl;
    });
    setIsUploading(false);

    if (!token) {
      setJobError("No encontramos tu sesion para crear clips automaticos. Volve a iniciar sesion.");
      return;
    }

    setIsCreatingJobs(true);

    try {
      const autoJobs = await videoApi.createAutoReframeJobs(uploaded.video_id, token);
      setCreatedJobs(autoJobs.jobs);
      setAutoJobCount(autoJobs.total_jobs);
    } catch (error) {
      setJobError(normalizeVideoError(error, "No pudimos crear los clips automaticos."));
    } finally {
      setIsCreatingJobs(false);
    }
  };

  const showPreview = Boolean(videoPreviewUrl && hasVideo && !isUploading);
  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel variant="accent" className="p-4 sm:p-5">
          <UploadDropzone
            onUpload={handleUpload}
            isUploading={isUploading}
            fileName={uploadedVideo?.filename}
          />
        </Panel>

        <Panel>
          <ProjectStatusPanel
            hasVideo={hasVideo}
            isUploading={isUploading}
            uploadError={uploadError}
            videoId={uploadedVideo?.video_id ?? null}
            isCreatingJobs={isCreatingJobs}
            jobsCreated={autoJobCount}
            jobError={jobError}
          />
        </Panel>
      </div>
      {showPreview && (<div className="mt-5 flex flex-col gap-5 lg:flex-row">
        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">timeline</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Preview y recorte</h3>
          <VideoPreview
            videoPreviewUrl={videoPreviewUrl}
            onTrimChange={(start, end) => {
              console.log("Enviar al backend:", { start, end });
            }}
          />
        </Panel>
        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">configuracion</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Ajustes de recorte</h3>
          <VideoSettings />
        </Panel>
      </div>)}

      <Panel className="mt-5">
        <GeneratedClipsSection clips={visibleClips} showLoading={isUploading || isCreatingJobs} />
      </Panel>
    </section>
  );
}
