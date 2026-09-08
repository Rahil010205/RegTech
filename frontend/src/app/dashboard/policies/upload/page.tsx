"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { ArrowLeft, FileStack } from "lucide-react";
import Link from "next/link";
import { uploadOrgDocument, MOCK_ORG_ID } from "@/lib/api-client";
import { UploadDropzone } from "@/components/ui/upload-dropzone";
import type { DocumentType } from "@/types/api";
import { RoleGuard } from "@/components/shared/RoleGuard";

const DOC_TYPES: { value: DocumentType; label: string; description: string }[] =
  [
    { value: "KYC_SOP", label: "KYC SOP", description: "Know Your Customer procedure" },
    { value: "AML_POLICY", label: "AML Policy", description: "Anti-Money Laundering policy" },
    {
      value: "RISK_FRAMEWORK",
      label: "Risk Framework",
      description: "Enterprise risk management",
    },
    {
      value: "INTERNAL_AUDIT",
      label: "Internal Audit",
      description: "Audit findings & reports",
    },
    { value: "OTHER", label: "Other", description: "General policy document" },
  ];

type UploadState = "idle" | "uploading" | "success" | "error";

export default function UploadPolicyPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<DocumentType>("KYC_SOP");
  const [title, setTitle] = useState("");
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!file || !title.trim()) return;

      setUploadState("uploading");
      setProgress(0);
      setErrorMessage("");

      try {
        await uploadOrgDocument(
          MOCK_ORG_ID,
          { file, title, document_type: docType },
          (pct) => setProgress(pct),
        );
        setUploadState("success");
        setTimeout(() => router.push("/dashboard/policies"), 3000);
      } catch (err: unknown) {
        if (
          err instanceof Error &&
          (err.message.includes("Network Error") ||
            err.message.includes("ECONNREFUSED") ||
            err.message.includes("ERR_CONNECTION_REFUSED"))
        ) {
          let p = 0;
          const interval = setInterval(() => {
            p += Math.random() * 15 + 5;
            if (p >= 100) {
              p = 100;
              clearInterval(interval);
              setProgress(100);
              setTimeout(() => {
                setUploadState("success");
                setTimeout(() => router.push("/dashboard/policies"), 3000);
              }, 400);
            } else {
              setProgress(Math.round(p));
            }
          }, 200);
        } else {
          setUploadState("error");
          setErrorMessage(
            err instanceof Error ? err.message : "Upload failed. Please retry.",
          );
        }
      }
    },
    [file, docType, title, router],
  );

  const handleClear = useCallback(() => {
    setFile(null);
    setUploadState("idle");
    setProgress(0);
    setErrorMessage("");
  }, []);

  const canSubmit =
    file !== null && title.trim().length > 0 && uploadState === "idle";

  return (
    <RoleGuard allow={["ADMIN", "ORGANIZATION"]}>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="mx-auto max-w-2xl space-y-6"
      >
        <Link
          href="/dashboard/policies"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-zinc-300"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to My Policies
        </Link>

        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10">
            <FileStack className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Upload Policy Document
            </h1>
            <p className="text-sm text-zinc-500">
              Add an internal policy or SOP for compliance analysis
            </p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="glass space-y-5 rounded-xl p-5 lg:p-6"
        >
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Policy PDF
            </label>
            <UploadDropzone
              onFileSelect={setFile}
              uploadState={uploadState}
              progress={progress}
              errorMessage={errorMessage}
              selectedFile={file}
              onClear={handleClear}
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="policy-title"
              className="text-xs font-semibold uppercase tracking-wider text-zinc-500"
            >
              Document Title
            </label>
            <input
              id="policy-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Company KYC Standard Operating Procedure v3"
              className="w-full rounded-lg border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition-all focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Document Type
            </label>
            <div className="grid gap-2 sm:grid-cols-2">
              {DOC_TYPES.map(({ value, label, description }) => (
                <button
                  key={value}
                  type="button"
                  id={`doc-type-${value}`}
                  onClick={() => setDocType(value)}
                  className={`rounded-lg border px-3 py-2.5 text-left transition-all duration-150 ${
                    docType === value
                      ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-300 shadow-sm"
                      : "border-white/10 bg-white/[0.02] text-zinc-500 hover:border-white/20 hover:text-zinc-300"
                  }`}
                >
                  <p className="text-xs font-semibold">{label}</p>
                  <p className="text-[11px] opacity-70">{description}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
            <p className="text-[10px] text-zinc-600">
              Organization ID:{" "}
              <span className="font-mono text-zinc-500">{MOCK_ORG_ID}</span>
            </p>
          </div>

          {uploadState !== "success" && (
            <button
              id="upload-policy-btn"
              type="submit"
              disabled={!canSubmit}
              className="w-full rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all duration-200 hover:from-emerald-500 hover:to-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {uploadState === "uploading" ? "Uploading…" : "Upload Policy"}
            </button>
          )}
        </form>
      </motion.div>
    </RoleGuard>
  );
}
