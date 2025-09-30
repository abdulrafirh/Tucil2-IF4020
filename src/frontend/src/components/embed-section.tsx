"use client"

import { useState } from "react"
import { Upload, Settings, Lock, Shuffle, Play, Zap, Key, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileUpload } from "@/components/file-upload"

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
  const [stegoKey, setStegoKey] = useState("")
  const [useEncryption, setUseEncryption] = useState(true)
  const [useRandomStart, setUseRandomStart] = useState(true)
  const [lsbBits, setLsbBits] = useState("2")
  const [customFileName, setCustomFileName] = useState("")

  const handleEmbed = async () => {
    if (!audioFile || !secretFile || !stegoKey) return

    onProcessingStart()

    // Simulate processing with realistic timing
    setTimeout(() => {
      const psnr = Math.random() * 20 + 30 // Random PSNR between 30-50 dB
      onResults({
        type: "embed",
        originalSize: audioFile.size,
        stegoSize: audioFile.size + secretFile.size * 0.1,
        psnr: Number.parseFloat(psnr.toFixed(1)),
        capacity: `${secretFile.size} / ${Math.floor(audioFile.size * 0.125)} bytes`,
        success: true,
        fileName: customFileName || `stego_${audioFile.name}`,
        settings: {
          encryption: useEncryption,
          randomStart: useRandomStart,
          lsbBits: Number.parseInt(lsbBits),
        },
      })
    }, 3000)
  }

  const canEmbed = audioFile && secretFile && stegoKey.length > 0

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
          Hide your secret file inside an MP3 audio file using advanced steganography
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* File Uploads */}
        <div className="grid md:grid-cols-2 gap-4 mobile-stack">
          <div className="slide-down">
            <FileUpload
              label="Cover Audio (MP3)"
              accept=".mp3"
              file={audioFile}
              onFileSelect={setAudioFile}
              icon={<Upload className="h-4 w-4" />}
            />
          </div>
          <div className="slide-down fade-in-delay">
            <FileUpload
              label="Secret File"
              accept="*"
              file={secretFile}
              onFileSelect={setSecretFile}
              icon={<Lock className="h-4 w-4" />}
            />
          </div>
        </div>

        {audioFile && secretFile && (
          <div className="space-y-6 slide-up">
            <div className="flex items-center gap-3 mb-4 p-4 bg-primary/5 rounded-xl border border-primary/20">
              <div className="p-2 bg-primary/10 rounded-lg float">
                <Settings className="h-4 w-4 text-primary" />
              </div>
              <Label className="text-base font-semibold text-primary">Steganography Settings</Label>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="stego-key" className="flex items-center gap-2 font-medium">
                  <Key className="h-4 w-4 text-primary" />
                  Stego Key
                </Label>
                <Input
                  id="stego-key"
                  type="password"
                  placeholder="Enter your secret key..."
                  value={stegoKey}
                  onChange={(e) => setStegoKey(e.target.value)}
                  className="bg-input border-border focus:ring-primary focus:border-primary transition-all duration-200 hover-glow"
                />
                <p className="text-xs text-muted-foreground">Used for encryption and random positioning</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="lsb-bits" className="flex items-center gap-2 font-medium">
                  <Zap className="h-4 w-4 text-primary" />
                  LSB Bits
                </Label>
                <Select value={lsbBits} onValueChange={setLsbBits}>
                  <SelectTrigger className="bg-input border-border focus:ring-primary hover-glow transition-all duration-200">
                    <SelectValue />
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

            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-primary/5 to-accent/5 rounded-xl border border-primary/20 hover-lift transition-all duration-300">
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
                <Switch
                  id="encryption"
                  checked={useEncryption}
                  onCheckedChange={setUseEncryption}
                  className="data-[state=checked]:bg-primary"
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-accent/5 to-primary/5 rounded-xl border border-primary/20 hover-lift transition-all duration-300">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Shuffle className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <Label htmlFor="random-start" className="font-medium text-foreground">
                      Random Start Position
                    </Label>
                    <p className="text-xs text-muted-foreground">Use seed-based random positioning</p>
                  </div>
                </div>
                <Switch
                  id="random-start"
                  checked={useRandomStart}
                  onCheckedChange={setUseRandomStart}
                  className="data-[state=checked]:bg-primary"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="custom-name" className="font-medium">
                Output File Name (optional)
              </Label>
              <Input
                id="custom-name"
                placeholder={`stego_${audioFile.name}`}
                value={customFileName}
                onChange={(e) => setCustomFileName(e.target.value)}
                className="bg-input border-border focus:ring-primary focus:border-primary transition-all duration-200 hover-glow"
              />
            </div>

            <Button
              onClick={handleEmbed}
              disabled={!canEmbed || isProcessing}
              className={`btn-creative w-full text-primary-foreground font-semibold py-4 text-lg relative overflow-hidden transition-all duration-300 ${
                isProcessing ? "pulse-green animate-pulse" : "hover-lift"
              }`}
              size="lg"
            >
              {isProcessing && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent shimmer" />
              )}
              <div className="relative z-10 flex items-center justify-center gap-3">
                {isProcessing ? (
                  <>
                    <div className="spinner-green w-5 h-5" />
                    <span>Embedding Magic in Progress...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5" />
                    <span>Embed Secret Message</span>
                    <Play className="h-4 w-4" />
                  </>
                )}
              </div>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
