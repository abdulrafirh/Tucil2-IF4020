"use client"

import { useState } from "react"
import { Upload, Settings, Lock, Play, Zap, Key, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileUpload } from "@/components/file-upload"
import { embedApi, capacityApi } from "@/lib/api"

interface EmbedSectionProps {
  audioFile: File | null
  setAudioFile: (file: File | null) => void
  secretFile: File | null
  setSecretFile: (file: File | null) => void
  onResults: (results: any) => void
  onProcessingStart: () => void
  isProcessing: boolean
}

export function EmbedSection({
  audioFile,
  setAudioFile,
  secretFile,
  setSecretFile,
  onResults,
  onProcessingStart,
  isProcessing,
}: EmbedSectionProps) {
  const [lsbBits, setLsbBits] = useState<string>("4")
  const [stegoKey, setStegoKey] = useState<string>("")
  const [useEncryption, setUseEncryption] = useState<boolean>(false)
  const [customFileName, setCustomFileName] = useState<string>("")

  const bitsPerFrame = Number.parseInt(lsbBits) || 4

  const handleCheckCapacity = async () => {
    if (!audioFile) return
    onProcessingStart()
    try {
      const cap = await capacityApi({
        carrier: audioFile,
        bitsPerFrame,
        vigenere: useEncryption, // echoed back; does not affect capacity
        payloadSize: secretFile ? secretFile.size : undefined,
      })

      onResults({
        type: "capacity",
        success: true,
        fileName: audioFile.name,
        capacityBytes: cap.capacity_bytes,
        usableBytes: cap.usable_payload_bytes,
        headerBytes: cap.header_size_bytes,
        fits: cap.fits,
        settings: {
          lsbBits: bitsPerFrame,
          encryption: useEncryption,
        },
      })
    } catch (err: any) {
      onResults({
        type: "capacity",
        success: false,
        error: err?.message || "Capacity check failed",
      })
    }
  }

  const handleEmbed = async () => {
    if (!audioFile || !secretFile) return
    onProcessingStart()
    try {
      const { stegoFile, psnr, stegoSize } = await embedApi({
        carrier: audioFile,
        payload: secretFile,
        bitsPerFrame,
        key: stegoKey,
        vigenere: useEncryption,
      })

      onResults({
        type: "embed",
        success: true,
        originalSize: audioFile.size,
        stegoSize,
        psnr: Number.isFinite(psnr) ? Number(psnr.toFixed(1)) : psnr,
        fileName: customFileName || stegoFile.name,
        stegoFile,
        settings: {
          encryption: useEncryption,
          lsbBits: bitsPerFrame,
        },
      })
    } catch (err: any) {
      onResults({
        type: "embed",
        success: false,
        error: err?.message || "Embed failed",
      })
    }
  }

  return (
    <Card className="border-primary/20 bg-gradient-to-b from-background via-background to-primary/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5 text-primary" />
          Embed
        </CardTitle>
        <CardDescription>Hide a file inside your MP3 using LSB on sign-bits</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Carrier MP3 */}
        <FileUpload
          label="Carrier Audio (MP3)"
          accept=".mp3,audio/mpeg"
          file={audioFile}
          onFileSelect={setAudioFile}
          icon={<MusicNoteIcon />}
        />

        {/* Secret file */}
        <FileUpload
          label="Secret File"
          accept="*"
          file={secretFile}
          onFileSelect={setSecretFile}
          icon={<Lock className="h-5 w-5" />}
        />

        {/* Settings */}
        <div className="rounded-lg border p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" />
            <h4 className="font-medium">Settings</h4>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
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
            </div>

            <div className="space-y-2">
              <Label htmlFor="key">Key</Label>
              <div className="flex items-center gap-2">
                <Key className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="key"
                  placeholder="Optional key"
                  value={stegoKey}
                  onChange={(e) => setStegoKey(e.target.value)}
                />
              </div>
              <p className="text-xs text-muted-foreground">Used for deterministic selection and (optionally) Vigenère</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between rounded-md border p-3">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4" />
                <div>
                  <p className="text-sm font-medium">Vigenère</p>
                  <p className="text-xs text-muted-foreground">Repeating-key XOR</p>
                </div>
              </div>
              <Switch checked={useEncryption} onCheckedChange={setUseEncryption} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="filename">Output name (optional)</Label>
              <Input
                id="filename"
                placeholder="stego.mp3"
                value={customFileName}
                onChange={(e) => setCustomFileName(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        {audioFile && secretFile && (
          <div className="grid md:grid-cols-2 gap-3">
            <Button
              onClick={handleCheckCapacity}
              variant="secondary"
              disabled={isProcessing}
              className={`w-full ${isProcessing ? "opacity-70 cursor-not-allowed" : ""}`}
            >
              <Zap className="h-4 w-4 mr-2" />
              Check Capacity
            </Button>

            <Button
              onClick={handleEmbed}
              disabled={isProcessing}
              className={`w-full bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200 ${
                isProcessing ? "pulse-green" : "hover:glow-green"
              }`}
              size="lg"
            >
              {isProcessing ? (
                <>
                  <Sparkles className="h-5 w-5 animate-pulse" />
                  <span>Embedding…</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5" />
                  <span>Embed Secret Message</span>
                  <Play className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function MusicNoteIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 text-primary" fill="currentColor">
      <path d="M12 3v10.55A4 4 0 1 1 10 17V7h8V3h-6z" />
    </svg>
  )
}
