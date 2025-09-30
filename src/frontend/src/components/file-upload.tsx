"use client"

import type React from "react"

import { useRef, useState } from "react"
import { Upload, File, X, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"

interface FileUploadProps {
  label: string
  accept: string
  file: File | null
  onFileSelect: (file: File | null) => void
  icon?: React.ReactNode
}

export function FileUpload({ label, accept, file, onFileSelect, icon }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploaded, setIsUploaded] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null
    onFileSelect(selectedFile)
    if (selectedFile) {
      setIsUploaded(true)
      setTimeout(() => setIsUploaded(false), 1000)
    }
  }

  const handleRemoveFile = () => {
    onFileSelect(null)
    if (inputRef.current) {
      inputRef.current.value = ""
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      onFileSelect(droppedFile)
      setIsUploaded(true)
      setTimeout(() => setIsUploaded(false), 1000)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <div className="space-y-2">
      <Label className="text-foreground font-medium">{label}</Label>

      {!file ? (
        <Card
          className={`border-2 border-dashed transition-all duration-300 cursor-pointer hover-lift relative overflow-hidden ${
            isDragOver
              ? "border-primary bg-primary/5 glow-green-strong scale-105"
              : "border-border hover:border-primary/50 hover:bg-primary/5"
          }`}
          onClick={() => inputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="absolute inset-0 shimmer opacity-50" />

          <div className="relative p-8 text-center space-y-4">
            <div
              className={`p-4 bg-primary/10 rounded-xl w-fit mx-auto transition-all duration-300 ${
                isDragOver ? "scale-110 rotate-12" : "hover:scale-105"
              }`}
            >
              {icon || <Upload className="h-6 w-6 text-primary" />}
            </div>
            <div>
              <p className="font-medium text-foreground">
                {isDragOver ? "Drop your file here!" : `Click to upload ${label.toLowerCase()}`}
              </p>
              <p className="text-sm text-muted-foreground">
                {accept === "*" ? "Any file type" : accept.toUpperCase()} files supported
              </p>
              <p className="text-xs text-primary/70 mt-1">Or drag and drop your file here</p>
            </div>
          </div>
        </Card>
      ) : (
        <Card
          className={`border-border bg-card hover-glow transition-all duration-300 ${
            isUploaded ? "bounce-in success-pulse" : ""
          }`}
        >
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded-lg relative">
                {isUploaded ? (
                  <CheckCircle className="h-4 w-4 text-primary animate-pulse" />
                ) : (
                  <File className="h-4 w-4 text-primary" />
                )}
              </div>
              <div>
                <p className="font-medium text-sm text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemoveFile}
              className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={accept === "*" ? undefined : accept}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  )
}
