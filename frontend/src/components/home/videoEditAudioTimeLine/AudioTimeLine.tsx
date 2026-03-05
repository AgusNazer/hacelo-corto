"use client";

import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";

type PropTimeLine = {
  videoDurationSec: number;
  selectedAudioUrl: string | null;
  regionChange?: (start: number, end: number) => void;
};

function secondsToLabel(value: number) {
  const safe = Math.max(0, Math.floor(value));
  const minutes = Math.floor(safe / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(safe % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function toRgbaFromHex(color: string, alpha: number) {
  const hex = color.trim();
  const normalized = hex.startsWith("#") ? hex.slice(1) : hex;
  const valid = normalized.length === 6;
  if (!valid) {
    return `rgba(137, 220, 235, ${alpha})`;
  }

  const r = Number.parseInt(normalized.slice(0, 2), 16);
  const g = Number.parseInt(normalized.slice(2, 4), 16);
  const b = Number.parseInt(normalized.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function AudioTimeLine({ videoDurationSec, selectedAudioUrl, regionChange }: PropTimeLine) {
  const wsRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<InstanceType<typeof RegionsPlugin> | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const regionRef = useRef<ReturnType<InstanceType<typeof RegionsPlugin>["addRegion"]> | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [selection, setSelection] = useState({ start: 0, end: 0 });

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    containerRef.current.innerHTML = "";
    const styles = getComputedStyle(document.documentElement);
    const neonCyan = styles.getPropertyValue("--hc-neon-cyan") || "#89dceb";
    const neonMagenta = styles.getPropertyValue("--hc-neon-magenta") || "#f5c2e7";
    const neonViolet = styles.getPropertyValue("--hc-neon-violet") || "#cba6f7";

    const regions = RegionsPlugin.create();
    const ws = WaveSurfer.create({
      container: containerRef.current,
      height: 72,
      barWidth: 3,
      barGap: 2,
      barRadius: 999,
      cursorWidth: 2,
      normalize: true,
      waveColor: toRgbaFromHex(neonCyan, 0.4),
      progressColor: toRgbaFromHex(neonMagenta, 0.7),
      cursorColor: toRgbaFromHex(neonViolet, 0.95),
      plugins: [regions]
    });

    ws.on("play", () => setIsPlaying(true));
    ws.on("pause", () => setIsPlaying(false));
    ws.on("finish", () => setIsPlaying(false));

    wsRef.current = ws;
    regionsRef.current = regions;

    return () => {
      try {
        ws.destroy();
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          throw error;
        }
      } finally {
        wsRef.current = null;
        regionsRef.current = null;
        regionRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const ws = wsRef.current;
    const regions = regionsRef.current;

    if (!ws || !regions || !selectedAudioUrl) {
      return;
    }

    let cancelled = false;
    ws.stop();
    setIsPlaying(false);
    ws.load(selectedAudioUrl);

    ws.once("ready", () => {
      if (cancelled) {
        return;
      }

      const audioDuration = ws.getDuration();
      if (!Number.isFinite(audioDuration) || audioDuration <= 0) {
        return;
      }

      regions.clearRegions();
      const maxRegionLength = Math.max(Math.min(videoDurationSec, audioDuration), 0.5);
      const minRegionLength = Math.min(5, maxRegionLength);

      const region = regions.addRegion({
        start: 0,
        end: maxRegionLength,
        minLength: minRegionLength,
        maxLength: maxRegionLength,
        color: "rgba(203, 166, 247, 0.25)",
        drag: true,
        resize: true
      });

      regionRef.current = region;
      const nextStart = Math.floor(region.start);
      const nextEnd = Math.floor(region.end);
      setSelection({ start: nextStart, end: nextEnd });
      regionChange?.(nextStart, nextEnd);

      region.on("update-end", () => {
        if (cancelled) {
          return;
        }
        const start = Math.floor(region.start);
        const end = Math.floor(region.end);
        setSelection({ start, end });
        regionChange?.(start, end);
      });
    });

    return () => {
      cancelled = true;
    };
  }, [selectedAudioUrl, videoDurationSec, regionChange]);

  const playRegion = () => {
    const ws = wsRef.current;
    const region = regionRef.current;

    if (!ws || !region) {
      return;
    }

    if (ws.isPlaying()) {
      ws.pause();
      return;
    }

    ws.play(region.start, region.end);
  };

  return (
    <div className="mt-4 rounded-xl border border-white/12 bg-white/5 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] uppercase tracking-[0.14em] text-neon-violet/90">Seleccion de audio</p>
        <p className="text-[11px] text-white/70">
          {secondsToLabel(selection.start)} - {secondsToLabel(selection.end)}
        </p>
      </div>

      <div className="mt-2 overflow-hidden rounded-lg border border-white/10 bg-night-900/70 px-2 py-2">
        <div ref={containerRef} />
      </div>

      <div className="mt-2 flex items-center justify-between gap-3">
        <p className="text-[11px] text-white/60">Arrastra y redimensiona la region para elegir el tramo.</p>
        <button
          type="button"
          onClick={playRegion}
          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-neon-violet/45 bg-neon-violet/15 text-neon-violet transition hover:bg-neon-violet/25"
          aria-label={isPlaying ? "Pausar audio" : "Reproducir audio"}
        >
          {isPlaying ? <Pause size={15} /> : <Play size={15} className="ml-0.5" />}
        </button>
      </div>
    </div>
  );
}
