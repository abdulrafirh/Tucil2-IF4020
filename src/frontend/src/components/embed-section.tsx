"use client"

import { useState } from "react"
import { Upload, Settings, Lock, Play, Zap, Key, Music } from "lucide-react"
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
        customName: customFileName
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
    <Card className="border-border bg-card shadow-lg hover-glow transition-all duration-300">
      <CardHeader className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="grid-background h-full w-full" />
        </div>
        <CardTitle className="flex items-center gap-2 text-primary relative z-10">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Upload className="h-5 w-5" />
          </div>
          Embed Secret Message
        </CardTitle>
        <CardDescription className="relative z-10">
          Hide a file inside your MP3 using LSB Steganography on sign-bits
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">

        <div className="slide-left fade-in-delay">
          {/* Carrier MP3 */}
          <FileUpload
            label="Carrier Audio (MP3)"
            accept=".mp3,audio/mpeg"
            file={audioFile}
            onFileSelect={setAudioFile}
            icon={<Music className="h-5 w-5 text-primary"/>}
          />
        </div>

        <div className="slide-left fade-in-delay delay-1000">
          {/* Secret file */}
          <FileUpload
            label="Secret File"
            accept="*"
            file={secretFile}
            onFileSelect={setSecretFile}
            icon={<Lock className="h-5 w-5 text-primary"/>}
          />
        </div>

        {audioFile && secretFile && (
          <div className="space-y-6 slide-down fade-in-delay delay-2000">
            <div className="rounded-lg border p-4 space-y-4 shadow-sm">
              <div className="flex items-center gap-3 mb-4 p-4 bg-primary/5 rounded-xl border border-primary/20">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Settings className="h-4 w-4 text-primary animate-[spin_6000ms_linear_infinite]" />
                </div>
                <Label className="text-base font-semibold text-primary">Steganography Settings</Label>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="stego-key" className="flex items-center gap-2 font-medium">
                    <Key className="h-4 w-4 text-primary" />
                    Stego Key
                  </Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="key"
                      placeholder="Optional Secret Key"
                      value={stegoKey}
                      onChange={(e) => setStegoKey(e.target.value)}
                      className="bg-input border-border focus:ring-primary focus:border-primary transition-all duration-200 hover-glow"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">Used for random positioning and Vigenère</p>
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
                </div>
              </div>

              <div className="col-span-2 flex items-center justify-between p-4 bg-gradient-to-r from-primary/5 to-accent/5 rounded-xl border border-primary/20 hover-lift transition-all duration-300">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Lock className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <Label htmlFor="encryption" className="font-medium text-foreground">
                      Vigenère Encryption
                    </Label>
                    <p className="text-xs text-muted-foreground">Encrypt secret data before embedding</p>
                  </div>
                </div>
                <Switch checked={useEncryption} onCheckedChange={setUseEncryption} className="data-[state=checked]:bg-primary"/>
              </div>

              <div className="col-span-2 space-y-2">
                <Label htmlFor="custom-name" className="font-medium">
                  Output File Name (optional)
                </Label>
                <Input
                  id="filename"
                  placeholder="stego_output.mp3"
                  value={customFileName}
                  onChange={(e) => setCustomFileName(e.target.value)}
                  className="bg-input border-border focus:ring-primary focus:border-primary transition-all duration-200 hover-glow"
                />
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-3">
              <Button
                onClick={handleCheckCapacity}
                variant="secondary"
                disabled={isProcessing}
                className={`text-foreground w-full font-semibold py-4 text-lg relative overflow-hidden transition-all duration-300  ${
                  isProcessing ? "opacity-70 animate-pulse cursor-not-allowed" : "hover-lift"
                }`}
              >
                <Zap className="h-4 w-4 mr-2" />
                Check Capacity
              </Button>

              <Button
                onClick={handleEmbed}
                disabled={isProcessing}
                className={`btn-creative w-full text-primary-foreground font-semibold py-4 text-lg relative overflow-hidden transition-all duration-300 ${
                  isProcessing ? "pulse-green animate-pulse" : "hover-lift"
                }`}
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Play className="h-5 w-5 animate-pulse" />
                    <span>Embedding…</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    <span>Embed Secret Message</span>
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
