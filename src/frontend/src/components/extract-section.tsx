"use client"

import { useState } from "react"
import { Download, Key, Play, Lock, Music, Zap } from "lucide-react"
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
    <Card className="border-border bg-card shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Download className="h-5 w-5" />
          </div>
          Extract Secret Message
        </CardTitle>
        <CardDescription>Recover a hidden file from a steganography embedded MP3</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">

        {/* Stego MP3 */}
        <div className="slide-right fade-in-delay">
          <FileUpload
            label="Stego Audio (MP3)"
            accept=".mp3,audio/mpeg"
            file={audioFile}
            onFileSelect={setAudioFile}
            icon={<Music className="h-5 w-5 text-primary"/>}
          />
        </div>

        {audioFile && (
        <div className="space-y-6 slide-down fade-in-delay delay-1000">
          <div className="rounded-lg border p-4 space-y-4 shadow-sm">
            <div className="flex items-center gap-3 mb-4 p-4 bg-primary/5 rounded-xl border border-primary/20">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Key className="h-4 w-4 text-primary animate-[rotate-wave_6s_ease-in-out_infinite]" />
              </div>
              <Label className="text-base font-semibold text-primary">Extraction Settings</Label>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                  <Label htmlFor="stego-key" className="flex items-center gap-2 font-medium">
                    <Key className="h-4 w-4 text-primary" />
                    Stego Key
                  </Label>
                  <Input
                    id="key"
                    placeholder="Key used during embedding"
                    value={stegoKey}
                    onChange={(e) => setStegoKey(e.target.value)}
                    className="bg-input border-border focus:ring-primary focus:border-primary transition-all duration-200 hover-glow"
                  />
              </div>

              <div className="space-y-2">
                <Label htmlFor="lsb-bits" className="flex items-center gap-2 font-medium">
                  <Zap className="h-4 w-4 text-primary" />
                  LSB Bits
                </Label>
                <Select value={lsbBits} onValueChange={setLsbBits}>
                  <SelectTrigger id="bits" className="bg-input border-border focus:ring-primary hover-glow transition-all duration-200">
                    <SelectValue placeholder="Select bits per frame" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 bit (Highest quality)</SelectItem>
                    <SelectItem value="2">2 bits (Balanced)</SelectItem>
                    <SelectItem value="3">3 bits (More capacity)</SelectItem>
                    <SelectItem value="4">4 bits (Maximum capacity)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">Must match the embedding settings.</p>
              </div>

              <div className="col-span-2 flex items-center justify-between p-4 bg-gradient-to-r from-primary/5 to-accent/5 rounded-xl border border-primary/20 hover-lift transition-all duration-300">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Lock className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <Label className="font-medium text-foreground">
                      Vigenère Encryption
                    </Label>
                    <p className="text-xs text-muted-foreground">For already Encrypted Secret Data using the same key for steganography</p>
                  </div>
                </div>
                <Switch checked={useEncryption} onCheckedChange={setUseEncryption} className="data-[state=checked]:bg-primary"/>
              </div>

              <div className="col-span-2 space-y-2">
                <Label htmlFor="outname" className="font-medium">
                  Extracted File Name (optional)
                </Label>
                <Input
                  id="outname"
                  placeholder="stego_message.txt"
                  value={customFileName}
                  onChange={(e) => setCustomFileName(e.target.value)}
                  className="bg-input border-border focus:ring-primary focus:border-primary transition-all duration-200 hover-glow"
                />
              </div>
            </div>
          </div>
          <div className="flex justify-end">
            <Button
              onClick={handleExtract}
              disabled={isProcessing}
              className={`btn-creative w-1/2 text-primary-foreground font-semibold py-4 text-lg relative overflow-hidden transition-all duration-300 ${
                  isProcessing ? "pulse-green animate-pulse" : "hover-lift"
                }`}
              size="lg"
            >
              {isProcessing ? (
                  <>
                    <Play className="h-5 w-5 animate-pulse" />
                    <span>Extracting…</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    <span>Extract Secret Message</span>
                  </>
                )}
            </Button>
          </div>
        </div>
      )}
      </CardContent>
    </Card>
  )
}
