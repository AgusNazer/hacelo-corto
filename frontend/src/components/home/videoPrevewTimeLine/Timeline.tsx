"use client";
import { useEffect, useRef, useState } from "react";
import { useVideoTrim } from "./useVideoTrim";

type Props = {
  duration: number;
  videoRef: React.RefObject<HTMLVideoElement | null>;
  onTrimChange?: (start: number, end: number) => void;
};

export function Timeline({
  duration,
  videoRef,
  onTrimChange,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  const [containerWidth, setContainerWidth] = useState(0);

  // medir ancho
  useEffect(() => {
    function update() {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    }

    update();
    window.addEventListener("resize", update);

    return () => window.removeEventListener("resize", update);
  }, []);

  const {
    startPx,
    endPx,
    playheadPx,
    pixelsPerSecond,
    startDrag,
    seek,
  } = useVideoTrim(
    duration,
    videoRef,
    containerWidth,
    onTrimChange
  );

  const startSec = startPx / pixelsPerSecond;
  const endSec = endPx / pixelsPerSecond;

  // marcas dinámicas
  const MAX_MARKS = 6;
  const step =
    duration <= MAX_MARKS
      ? 1
      : Math.ceil(duration / MAX_MARKS);

  const marks = [];
  for (let i = 0; i <= duration; i += step) {
    marks.push(i);
  }

  return (
    <div ref={containerRef} className="w-full mt-4">
      {/* tiempo */}
      <div className="flex justify-between text-xs text-white/60 mb-1">
        <span>{startSec.toFixed(2)}s</span>
        <span>{endSec.toFixed(2)}s</span>
      </div>

      {/* escala */}
      <div className="relative h-5 text-[10px] text-white/40">
        {marks.map((sec) => (
          <div
            key={sec}
            className="absolute top-0"
            style={{ left: sec * pixelsPerSecond }}
          >
            <div className="w-px h-2 bg-white/40 mx-auto" />
            <span>{Math.round(sec)}s</span>
          </div>
        ))}
      </div>

      {/* track */}
      <div
        ref={timelineRef}
        data-timeline
        onClick={seek}
        className="relative h-14 bg-white/10 rounded cursor-pointer"
      >
        <div
          className="absolute top-0 bottom-0 bg-blue-500/30"
          style={{
            left: startPx,
            width: endPx - startPx,
          }}
        />

        <div
          className="absolute top-0 bottom-0 w-[2px] bg-red-500"
          style={{ left: playheadPx }}
        />

        <div
          onMouseDown={() => startDrag("start")}
          className="absolute top-0 bottom-0 w-2 bg-white cursor-ew-resize"
          style={{ left: startPx }}
        />

        <div
          onMouseDown={() => startDrag("end")}
          className="absolute top-0 bottom-0 w-2 bg-white cursor-ew-resize"
          style={{ left: endPx }}
        />
      </div>
    </div>
  );
}
