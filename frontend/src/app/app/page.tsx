"use client";

import { GeneratedClipsSection, type Clip } from "@/src/components/home/GeneratedClipsSection";
import { ProjectStatusPanel } from "@/src/components/home/ProjectStatusPanel";
import { UploadDropzone } from "@/src/components/home/UploadDropzone";
import { Panel } from "@/src/components/ui/Panel";
import { useMemo, useState } from "react";

const mockClips: Clip[] = [
  { id: "clip-1", title: "Hook inicial", duration: "00:31", preset: "Impact", status: "listo" },
  { id: "clip-2", title: "Momento clave", duration: "00:24", preset: "Story", status: "revision" },
  { id: "clip-3", title: "CTA final", duration: "00:18", preset: "Fast Cut", status: "render" }
];

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export default function AppHomePage() {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const hasVideo = Boolean(selectedFile);
  const visibleClips = useMemo(() => (hasVideo && !isUploading ? mockClips : []), [hasVideo, isUploading]);

  const handleUpload = async (file: File) => {
    setSelectedFile(file);
    setIsUploading(true);
    await wait(1400);
    setIsUploading(false);
  };

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel variant="accent" className="p-4 sm:p-5">
          <UploadDropzone
            onUpload={handleUpload}
            isUploading={isUploading}
            fileName={selectedFile?.name}
          />
        </Panel>

        <Panel>
          <ProjectStatusPanel hasVideo={hasVideo} isUploading={isUploading} />
        </Panel>
      </div>

      <Panel className="mt-5">
        <GeneratedClipsSection clips={visibleClips} showLoading={isUploading} />
      </Panel>
    </section>
  );
}
