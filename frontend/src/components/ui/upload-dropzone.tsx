"use client";

import { useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, CheckCircle2, XCircle, File, X } from "lucide-react";
import { cn } from "@/lib/utils";

type UploadState = "idle" | "uploading" | "success" | "error";

interface UploadDropzoneProps {
  accept?: string;
  maxSizeMB?: number;
  onFileSelect: (file: File) => void;
  uploadState: UploadState;
  progress?: number;
  errorMessage?: string;
  selectedFile?: File | null;
  onClear?: () => void;
}

export function UploadDropzone({
  accept = "application/pdf",
  maxSizeMB = 50,
  onFileSelect,
  uploadState,
  progress = 0,
  errorMessage,
  selectedFile,
  onClear,
}: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      if (file.size > maxSizeMB * 1024 * 1024) {
        return;
      }
      onFileSelect(file);
    },
    [maxSizeMB, onFileSelect],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="relative">
      <AnimatePresence mode="wait">
        {uploadState === "success" ? (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex flex-col items-center justify-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-10"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.1, type: "spring", stiffness: 300 }}
            >
              <CheckCircle2 className="h-14 w-14 text-emerald-400" />
            </motion.div>
            <p className="text-lg font-semibold text-emerald-300">
              Upload Successful
            </p>
            <p className="text-sm text-emerald-400/70">
              Document is being processed in the background.
            </p>
          </motion.div>
        ) : uploadState === "uploading" ? (
          <motion.div
            key="uploading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center gap-4 rounded-xl border border-blue-500/30 bg-blue-500/10 p-10"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Upload className="h-10 w-10 text-blue-400" />
            </motion.div>
            <div className="w-full max-w-xs space-y-1.5">
              <div className="flex justify-between text-xs text-blue-300/70">
                <span>Uploading…</span>
                <span>{progress}%</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-blue-900/50">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400"
                  initial={{ width: "0%" }}
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: "easeOut" }}
                />
              </div>
            </div>
            <p className="text-sm text-blue-300/70">
              {selectedFile?.name ?? "Sending file…"}
            </p>
          </motion.div>
        ) : uploadState === "error" ? (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-10"
          >
            <XCircle className="h-12 w-12 text-red-400" />
            <p className="font-semibold text-red-300">Upload Failed</p>
            <p className="text-center text-sm text-red-400/70">
              {errorMessage ?? "An unexpected error occurred. Please try again."}
            </p>
            {onClear && (
              <button
                onClick={onClear}
                className="mt-1 rounded-lg border border-red-500/30 px-4 py-1.5 text-xs text-red-300 transition-colors hover:bg-red-500/20"
              >
                Try Again
              </button>
            )}
          </motion.div>
        ) : (
          <motion.label
            key="idle"
            htmlFor="file-upload-input"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-10 transition-all duration-200",
              isDragging
                ? "border-blue-400/60 bg-blue-500/10"
                : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]",
            )}
          >
            <input
              id="file-upload-input"
              type="file"
              accept={accept}
              className="sr-only"
              onChange={handleChange}
            />
            {selectedFile ? (
              <div className="flex flex-col items-center gap-2">
                <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2">
                  <File className="h-4 w-4 text-zinc-400" />
                  <span className="max-w-xs truncate text-sm text-zinc-300">
                    {selectedFile.name}
                  </span>
                  <span className="text-xs text-zinc-500">
                    ({(selectedFile.size / 1024 / 1024).toFixed(1)} MB)
                  </span>
                  {onClear && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        onClear();
                      }}
                      className="ml-1 text-zinc-500 hover:text-zinc-300"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <p className="text-xs text-zinc-500">
                  Click or drag to replace
                </p>
              </div>
            ) : (
              <>
                <div
                  className={cn(
                    "rounded-full p-4 transition-colors",
                    isDragging ? "bg-blue-500/20" : "bg-white/5",
                  )}
                >
                  <Upload
                    className={cn(
                      "h-8 w-8 transition-colors",
                      isDragging ? "text-blue-400" : "text-zinc-400",
                    )}
                  />
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-zinc-300">
                    Drop PDF here or{" "}
                    <span className="text-blue-400">browse</span>
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    PDF only · max {maxSizeMB}MB
                  </p>
                </div>
              </>
            )}
          </motion.label>
        )}
      </AnimatePresence>
    </div>
  );
}
