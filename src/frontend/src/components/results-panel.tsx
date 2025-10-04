"use client"

import {
  CheckCircle,
  Download,
  AlertCircle,
  FileText,
  Loader2,
  HardDrive,
  Gauge,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

interface ResultsPanelProps {
  results?: {
    type: "embed" | "extract" | "capacity"
    success: boolean
    // Embed
    stegoFile?: File
    fileName?: string
    originalSize?: number
    stegoSize?: number
    psnr?: number
    // Extract
    downloadFile?: File
    fileSize?: string
    fileType?: string
    extractedAt?: string
    // Capacity
    capacityBytes?: number
    usableBytes?: number
    headerBytes?: number
    fits?: boolean
    payload_size?: number
    settings?: {
      lsbBits?: number
      encryption?: boolean
      [k: string]: any
    }
    // Generic
    error?: string
  } | null
  isProcessing?: boolean
}

function formatBytes(n?: number) {
  if (n == null) return "-"
  const units = ["B", "KB", "MB", "GB"]
  let idx = 0
  let v = n
  while (v >= 1024 && idx < units.length - 1) {
    v /= 1024
    idx++
  }
  return `${v.toFixed(v < 10 && idx > 0 ? 1 : 0)} ${units[idx]}`
}

function handleDownload(file?: File, suggestedName?: string) {
  if (!file) return
  const url = URL.createObjectURL(file)
  const a = document.createElement("a")
  a.href = url
  a.download = suggestedName || file.name || "download"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function ResultsPanel({ results, isProcessing }: ResultsPanelProps) {
  // Processing state
  if (isProcessing) {
    return (
      <Card className="border-primary/20 slide-down">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            Working…
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Progress value={66} className="h-2" />
            <p className="text-sm text-muted-foreground">This usually takes a moment.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!results) return null

  // CAPACITY
  if (results.type === "capacity") {
    if (!results.success) {
      return (
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Capacity Check Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{results.error ?? "Unable to compute capacity."}</p>
          </CardContent>
        </Card>
      )
    }

    const capacity = results.capacityBytes ?? 0
    const usable = results.usableBytes ?? Math.max(capacity - (results.headerBytes ?? 16), 0)
    const header = results.headerBytes ?? 16
    const payload = typeof results.payload_size === "number" ? results.payload_size : undefined
    const pct = payload != null && usable > 0 ? Math.min(100, Math.max(0, (payload / usable) * 100)) : undefined

    return (
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-primary" />
            Capacity Check
            {typeof results.fits === "boolean" && (
              <Badge variant={results.fits ? "default" : "destructive"} className="ml-2">
                {results.fits ? "Fits" : "Too Large"}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Usable Payload" value={formatBytes(usable)} />
            <Stat label="Total Capacity" value={formatBytes(capacity)} />
            <Stat label="Header Size" value={formatBytes(header)} />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Bits/Frame" value={String(results.settings?.lsbBits ?? "-")} />
            <Stat
              label="Vigenère"
              value={results.settings?.encryption ? "On" : "Off"}
              valueClass={results.settings?.encryption ? "text-primary" : "text-muted-foreground"}
            />
            <Stat label="Carrier" value={results.fileName ?? "-"} />
          </div>

          {payload != null && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <Gauge className="h-4 w-4 text-primary" />
                  Usage
                </span>
                <span className="text-muted-foreground">
                  {formatBytes(payload)} / {formatBytes(usable)}
                </span>
              </div>
              <Progress value={pct ?? 0} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  // EMBED
  if (results.type === "embed") {
    return results.success ? (
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-primary" />
            Embedding Complete
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Original Size" value={formatBytes(results.originalSize)} />
            <Stat label="Stego Size" value={formatBytes(results.stegoSize)} />
            <Stat label="PSNR" value={results.psnr != null ? `${results.psnr.toFixed ? results.psnr.toFixed(1) : results.psnr} dB` : "-"} />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Bits/Frame" value={String(results.settings?.lsbBits ?? "-")} />
            <Stat
              label="Vigenère"
              value={results.settings?.encryption ? "On" : "Off"}
              valueClass={results.settings?.encryption ? "text-primary" : "text-muted-foreground"}
            />
            <Stat label="Output Name" value={results.fileName ?? "stego.mp3"} />
          </div>

          <div className="grid md:grid-cols-3 gap-3">
            <Button
              onClick={() => handleDownload(results.stegoFile, results.fileName)}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground glow-green transition-all duration-200"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Stego Audio
            </Button>
          </div>
        </CardContent>
      </Card>
    ) : (
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Embedding Failed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{results.error ?? "An error occurred while embedding."}</p>
        </CardContent>
      </Card>
    )
  }

  // EXTRACT
  if (results.type === "extract") {
    return results.success ? (
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-primary" />
            Extraction Complete
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="File Name" value={results.fileName ?? "-"} />
            <Stat label="File Size" value={results.fileSize ?? "-"} />
            <Stat label="Type" value={results.fileType ?? "-"} />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Bits/Frame" value={String(results.settings?.lsbBits ?? "-")} />
            <Stat
              label="Vigenère"
              value={results.settings?.encryption ? "On" : "Off"}
              valueClass={results.settings?.encryption ? "text-primary" : "text-muted-foreground"}
            />
            <Stat label="Extracted" value={results.extractedAt ?? "-"} />
          </div>

          <div className="grid md:grid-cols-3 gap-3">
            <Button
              onClick={() => handleDownload(results.downloadFile, results.fileName)}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground glow-green transition-all duration-200"
            >
              <Download className="h-4 w-4 mr-2" />
              Download Extracted File
            </Button>
          </div>
        </CardContent>
      </Card>
    ) : (
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Extraction Failed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{results.error ?? "Invalid key or no hidden message found."}</p>
        </CardContent>
      </Card>
    )
  }

  // Fallback (unknown type)
  return (
    <Card>
      <CardHeader>
        <CardTitle>Result</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">Nothing to display yet.</p>
      </CardContent>
    </Card>
  )
}

function Stat({
  label,
  value,
  valueClass,
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`text-sm font-medium truncate ${valueClass ?? ""}`}>{value}</p>
    </div>
  )
}
