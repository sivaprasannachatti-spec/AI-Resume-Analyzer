"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { Upload, AlertCircle, Sparkles, CheckCircle2, FileText, RefreshCw } from "lucide-react";

interface DropzoneProps {
  onFileSelected: (file: File | null) => void;
  selectedFile: File | null;
  isLoading?: boolean;
}

export default function ResumeDropzone({ onFileSelected, selectedFile, isLoading = false }: DropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFile = (file: File) => {
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Please select a PDF document (.pdf)");
      return;
    }

    // Immediately record file and display green tick mark without triggering backend request
    setErrorMsg(null);
    onFileSelected(file);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const resetUpload = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelected(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={onDrop}
        onClick={() => !isLoading && fileInputRef.current?.click()}
        className={`relative cursor-pointer rounded-2xl p-6 sm:p-8 transition-all duration-300 premium-card border-2 border-dashed flex flex-col items-center justify-center text-center group ${
          isDragOver
            ? "border-blue-500 bg-blue-50/30 dark:bg-blue-950/20 scale-[1.01]"
            : "border-slate-300 dark:border-slate-700 hover:border-blue-400 dark:hover:border-blue-500"
        } ${isLoading ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={onFileChange}
        />

        {selectedFile ? (
          // File selected state: Immediately displays file name and green tick mark with NO extraction yet
          <div className="flex flex-col items-center py-2 z-10 w-full max-w-md animate-in fade-in duration-200">
            {/* Immediate Green Tick Mark Circle */}
            <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/80 flex items-center justify-center mb-3 shadow-md shadow-emerald-500/10">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            {/* Immediate File Name Display */}
            <div className="flex items-center gap-2 max-w-full px-4 py-2 rounded-xl bg-slate-100/90 dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 mb-2">
              <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0" />
              <p className="font-bold text-slate-900 dark:text-white text-xs sm:text-sm truncate">
                {selectedFile.name}
              </p>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 shrink-0">
                ({formatFileSize(selectedFile.size)})
              </span>
            </div>

            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold flex items-center justify-center gap-1 mt-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              File selected! Processing starts when you click Generate Tailored Resume.
            </p>

            <button
              type="button"
              onClick={resetUpload}
              className="mt-2.5 inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 underline"
            >
              <RefreshCw className="w-3 h-3" /> Choose another file
            </button>
          </div>
        ) : (
          // Default empty dropzone
          <div className="flex flex-col items-center py-4 z-10">
            <div className="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform duration-300">
              <Upload className="w-7 h-7" />
            </div>
            <h4 className="text-base font-bold text-slate-900 dark:text-white mb-1">
              Upload Resume (PDF)
            </h4>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-sm">
              Drag and drop your file here, or <span className="text-blue-600 dark:text-blue-400 font-semibold underline underline-offset-2">browse files</span>
            </p>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-4 bg-slate-100 dark:bg-slate-800/80 px-3 py-1 rounded-full border border-slate-200/60 dark:border-slate-700/60">
              <Sparkles className="w-3 h-3 text-amber-500" />
              Instant selection • Processed on Generate
            </span>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="mt-3 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-400 text-xs flex items-center justify-between gap-2 animate-in fade-in duration-200">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="px-2.5 py-1 rounded-lg bg-rose-100 dark:bg-rose-900/80 text-rose-800 dark:text-rose-200 text-[11px] font-semibold hover:bg-rose-200 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
