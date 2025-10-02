"use client"

import { useState } from "react"
import { Download, Key, Play, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileUpload } from "@/components/file-upload"
import { extractApi } from "@/lib/api"

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
  const [lsbBits, setLsbBits] = useState<string>("4")
  const [stegoKey, setStegoKey] = useState<string>("")
  const [useEncryption, setUseEncryption] = useState<boolean>(false)
  const [customFileName, setCustomFileName] = useState<string>("")

  const bitsPerFrame = Number.parseInt(lsbBits) || 4

  const handleExtract = async () => {
    if (!audioFile) return
    onProcessingStart()
    try {
      const { file, filename, size, contentType } = await extractApi({
        stego: audioFile,
        bitsPerFrame,
        key: stegoKey,
        vigenere: useEncryption, // MUST match what was used during embed
        saveAs: customFileName || undefined,
      })

      onResults({
        type: "extract",
        success: true,
        fileName: filename,
        fileSize: `${(size / 1024).toFixed(1)} KB`,
        fileType: contentType,
        extractedAt: new Date().toLocaleString(),
        downloadFile: file,
        settings: {
          encryption: useEncryption,
          lsbBits: bitsPerFrame,
        },
      })
    } catch (err: any) {
      onResults({
        type: "extract",
        success: false,
        error: err?.message || "Extraction failed",
      })
    }
  }

  return (
    <Card className="border-primary/20 bg-gradient-to-b from-background via-background to-primary/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5 text-primary" />
          Extract
        </CardTitle>
        <CardDescription>Recover a hidden file from a stego MP3</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Stego MP3 */}
        <FileUpload
          label="Stego Audio (MP3)"
          accept=".mp3,audio/mpeg"
          file={audioFile}
          onFileSelect={setAudioFile}
          icon={<Download className="h-5 w-5" />}
        />

        {/* Settings */}
        <div className="rounded-lg border p-4 space-y-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="bits">Bits per Frame</Label>
              <Select value={lsbBits} onValueChange={setLsbBits}>
                <SelectTrigger id="bits">
                  <SelectValue placeholder="Select bits per frame" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1</SelectItem>
                  <SelectItem value="2">2</SelectItem>
                  <SelectItem value="3">3</SelectItem>
                  <SelectItem value="4">4</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Must match the embedding settings.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="key">Key</Label>
              <div className="flex items-center gap-2">
                <Key className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="key"
                  placeholder="Key used during embed"
                  value={stegoKey}
                  onChange={(e) => setStegoKey(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center justify-between rounded-md border p-3">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4" />
                <div>
                  <p className="text-sm font-medium">Vigenère</p>
                  <p className="text-xs text-muted-foreground">Must match embed</p>
                </div>
              </div>
              <Switch checked={useEncryption} onCheckedChange={setUseEncryption} />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="outname">Output name (optional)</Label>
            <Input
              id="outname"
              placeholder="recovered.bin"
              value={customFileName}
              onChange={(e) => setCustomFileName(e.target.value)}
            />
          </div>
        </div>

        {/* Action */}
        {audioFile && (
          <div className="grid">
            <Button
              onClick={handleExtract}
              disabled={isProcessing}
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
