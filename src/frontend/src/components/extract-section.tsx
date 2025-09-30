"use client"

import { useState } from "react"
import { Download, Key, Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { FileUpload } from "@/components/file-upload"

interface ExtractSectionProps {
  audioFile: File | null
  setAudioFile: (file: File | null) => void
  onResults: (results: any) => void
  onProcessingStart: () => void
  isProcessing: boolean
}

export function ExtractSection({
  audioFile,
  setAudioFile,
  onResults,
  onProcessingStart,
  isProcessing,
}: ExtractSectionProps) {
  const [stegoKey, setStegoKey] = useState("")
  const [customFileName, setCustomFileName] = useState("")

  const handleExtract = async () => {
    if (!audioFile || !stegoKey) return

    onProcessingStart()

    // Simulate processing with realistic timing
    setTimeout(() => {
      onResults({
        type: "extract",
        fileName: customFileName || "secret_document.pdf",
        fileSize: "2.4 MB",
        fileType: "PDF Document",
        extractedAt: new Date().toLocaleString(),
        success: true,
      })
    }, 2500)
  }

  const canExtract = audioFile && stegoKey.length > 0

  return (
    <Card className="border-border bg-card shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <Download className="h-5 w-5" />
          Extract Secret Message
        </CardTitle>
        <CardDescription>Extract hidden files from steganographic MP3 audio files</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* File Upload */}
        <FileUpload
          label="Stego Audio (MP3)"
          accept=".mp3"
          file={audioFile}
          onFileSelect={setAudioFile}
          icon={<Download className="h-4 w-4" />}
        />

        {audioFile && (
          <div className="space-y-4 fade-in">
            <div className="flex items-center gap-2 mb-4">
              <Key className="h-4 w-4 text-primary" />
              <Label className="text-base font-medium">Extraction Settings</Label>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="extract-key">Stego Key</Label>
                <Input
                  id="extract-key"
                  type="password"
                  placeholder="Enter the same key used for embedding..."
                  value={stegoKey}
                  onChange={(e) => setStegoKey(e.target.value)}
                  className="bg-input border-border focus:ring-primary"
                />
                <p className="text-xs text-muted-foreground">Must match the key used during embedding</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="extract-name">Save As (optional)</Label>
                <Input
                  id="extract-name"
                  placeholder="extracted_file"
                  value={customFileName}
                  onChange={(e) => setCustomFileName(e.target.value)}
                  className="bg-input border-border focus:ring-primary"
                />
              </div>
            </div>

            <Button
              onClick={handleExtract}
              disabled={!canExtract || isProcessing}
              className={`w-full bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200 ${
                isProcessing ? "pulse-green" : "hover:glow-green"
              }`}
              size="lg"
            >
              <Play className="h-4 w-4 mr-2" />
              {isProcessing ? "Extracting..." : "Extract Secret Message"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
