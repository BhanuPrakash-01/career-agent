// src/components/FileUpload.tsx
"use client";

import { useState } from "react";
import { Upload, FileText, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { uploadResume } from "@/lib/api";

interface FileUploadProps {
  userId: string; // Required to link data to the correct user in Supabase
  onUploadComplete: (data: any) => void; // Pass parsed data up to the parent
}

export default function FileUpload({ userId, onUploadComplete }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  // Handle Drag Events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  };

  // Handle Drop Event
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  // Handle Manual File Selection
  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  // Main Upload Logic
  const processFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setUploadStatus("error");
      setErrorMessage("Only PDF files are supported.");
      return;
    }

    setIsUploading(true);
    setUploadStatus("idle");
    setErrorMessage("");

    try {
      // Pass the file AND the userId to the backend
      const response = await uploadResume(file, userId);
      
      setUploadStatus("success");
      
      // Pass the parsed data (from Gemini) up to the parent component
      // The API returns { status: "success", data: { ... } }
      if (response && response.data) {
        onUploadComplete(response.data);
      } else {
        // Fallback if structure is unexpected
        onUploadComplete(response); 
      }

    } catch (error: any) {
      console.error("Upload failed:", error);
      setUploadStatus("error");
      setErrorMessage(error.response?.data?.detail || "Failed to upload resume.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div
      className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ease-in-out ${
        isDragging
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-gray-400 bg-white"
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      {/* Hidden Input for Click-to-Upload */}
      <input
        type="file"
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        onChange={handleChange}
        accept=".pdf"
        disabled={isUploading}
      />

      <div className="flex flex-col items-center justify-center space-y-4 pointer-events-none relative z-0">
        {/* ICON LOGIC */}
        {isUploading ? (
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
        ) : uploadStatus === "success" ? (
          <CheckCircle className="w-12 h-12 text-green-500" />
        ) : uploadStatus === "error" ? (
          <AlertCircle className="w-12 h-12 text-red-500" />
        ) : (
          <div className="bg-blue-100 p-4 rounded-full">
            <Upload className="w-8 h-8 text-blue-600" />
          </div>
        )}

        {/* TEXT LOGIC */}
        <div className="space-y-1">
          <p className="text-lg font-medium text-gray-700">
            {isUploading 
              ? "Analyzing your resume..." 
              : uploadStatus === "success" 
                ? "Resume Parsed Successfully!" 
                : uploadStatus === "error"
                  ? "Upload Failed"
                  : "Drop your PDF resume here"
            }
          </p>
          
          <p className="text-sm text-gray-500">
            {uploadStatus === "error" 
              ? errorMessage 
              : "We'll extract your experience and projects automatically."}
          </p>
        </div>
      </div>
    </div>
  );
}