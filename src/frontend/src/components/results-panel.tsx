"use client"

import { CheckCircle, Download, AlertCircle, FileText, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

interface ResultsPanelProps {
  results?: {
    type: "embed" | "extract"
    success: boolean
    [key: string]: any
  } | null
  isProcessing?: boolean
}

export function ResultsPanel({ results, isProcessing }: ResultsPanelProps) {
  const handleDownload = () => {
    // Simulate file download
    console.log("[v0] Downloading file...")
  }

  if (isProcessing) {
    return (
      <Card className="border-border bg-card shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Loader2 className="h-5 w-5 animate-spin" />
            Processing...
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center py-8">
            <div className="pulse-green rounded-full w-16 h-16 bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Loader2 className="h-8 w-8 text-primary animate-spin" />
            </div>
            <p className="text-muted-foreground">Processing your request...</p>
            <Progress value={undefined} className="mt-4" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!results) return null

  if (results.type === "embed") {
    return (
      <Card className="border-border bg-card shadow-lg success-bounce">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {results.success ? (
              <CheckCircle className="h-5 w-5 text-primary" />
            ) : (
              <AlertCircle className="h-5 w-5 text-destructive" />
            )}
            <span className="text-primary">Embedding Results</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {results.success ? (
            <>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <p className="text-muted-foreground">Original Size</p>
                  <p className="font-medium">{Math.round(results.originalSize / 1024)} KB</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Stego Size</p>
                  <p className="font-medium">{Math.round(results.stegoSize / 1024)} KB</p>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">PSNR Quality</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{results.psnr} dB</p>
                    <Badge
                      variant={results.psnr > 40 ? "default" : results.psnr > 30 ? "secondary" : "destructive"}
                      className="text-xs bg-primary/10 text-primary border-primary/20"
                    >
                      {results.psnr > 40 ? "Excellent" : results.psnr > 30 ? "Good" : "Poor"}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Capacity Used</p>
                  <p className="font-medium">{results.capacity}</p>
                </div>
              </div>

              <div className="pt-4 border-t border-border space-y-3">
                <div className="flex items-center gap-3 p-3 bg-primary/5 rounded-lg border border-primary/10">
                  <FileText className="h-8 w-8 text-primary" />
                  <div className="flex-1">
                    <p className="font-medium">{results.fileName}</p>
                    <p className="text-sm text-muted-foreground">Ready for download</p>
                  </div>
                </div>

                <Button
                  onClick={handleDownload}
                  className="w-full bg-primary hover:bg-primary/90 text-primary-foreground glow-green transition-all duration-200"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Stego Audio
                </Button>
              </div>
            </>
          ) : (
            <div className="text-center py-4">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-2" />
              <p className="text-destructive font-medium">Embedding Failed</p>
              <p className="text-sm text-muted-foreground">The secret file is too large for the selected audio file.</p>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-border bg-card shadow-lg success-bounce">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {results.success ? (
            <CheckCircle className="h-5 w-5 text-primary" />
          ) : (
            <AlertCircle className="h-5 w-5 text-destructive" />
          )}
          <span className="text-primary">Extraction Results</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {results.success ? (
          <>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-primary/5 rounded-lg border border-primary/10">
                <FileText className="h-8 w-8 text-primary" />
                <div className="flex-1">
                  <p className="font-medium">{results.fileName}</p>
                  <p className="text-sm text-muted-foreground">
                    {results.fileType} • {results.fileSize}
                  </p>
                </div>
              </div>

              <div className="text-sm text-muted-foreground">
                <p>Extracted: {results.extractedAt}</p>
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <Button
                onClick={handleDownload}
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground glow-green transition-all duration-200"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Extracted File
              </Button>
            </div>
          </>
        ) : (
          <div className="text-center py-4">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-2" />
            <p className="text-destructive font-medium">Extraction Failed</p>
            <p className="text-sm text-muted-foreground">Invalid key or no hidden message found.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
