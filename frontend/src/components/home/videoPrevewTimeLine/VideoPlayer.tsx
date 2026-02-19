"use client";
import { Pause, Play } from "lucide-react";
import { useEffect, useState } from "react";

type Props = {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  src: string | null;
  start?: number;
  end?: number;
};

export function VideoPlayer({
  videoRef,
  src,
  start = 0,
  end,
}: Props) {
  const [isPlaying, setIsPlaying] = useState(false);

  // =========================
  // Limitar reproducción al trim
  // =========================
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    function handleTimeUpdate() {
        if (!video) return;
      if (end !== undefined && video.currentTime >= end) {
        video.pause();
        video.currentTime = start;
        setIsPlaying(false);
      }
    }

    video.addEventListener("timeupdate", handleTimeUpdate);

    return () =>
      video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [start, end, videoRef]);

  // =========================
  // Play / Pause
  // =========================
  function togglePlay() {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      // arrancar desde el inicio del trim
      if (video.currentTime < start || video.currentTime > (end ?? Infinity)) {
        video.currentTime = start;
      }

      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }

  return (
    <div className=" relative mt-2 overflow-hidden rounded-lg border border-white/15 bg-black/40">
      
      {/* Video */}
      <video
        ref={videoRef}
        preload="metadata"
        className="w-full max-h-[400px] object-contain"
        src={src ?? undefined}
      />

      {/* Controls */}
      <div className="absolute  bottom-2 left-2 overflow-hidden rounded-lg border border-white/15 bg-black/40">
        {isPlaying?(<Pause size={25}
        onClick={togglePlay}/>): <Play size={25} onClick={togglePlay}/>}
        
      </div>
        
        
        {/* <StopCircleIcon/> */}
        {/* <button
          onClick={togglePlay}
          className="px-3 py-1 rounded bg-blue-500 hover:bg-blue-600 text-white text-sm"
        >
          {isPlaying ? "Pause" : "Play"}
        </button> */}
    </div>
  );
}
