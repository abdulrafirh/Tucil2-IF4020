"use client"

import { useState, useRef, useEffect } from "react"
import { Play, Pause, Volume2, SkipBack, SkipForward, Activity, Download, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"

interface AudioPlayerProps {
  file: File
  title: string
  psnr?: number
}

export function AudioPlayer({ file, title, psnr }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState([75])
  const audioRef = useRef<HTMLAudioElement>(null)
  const [audioUrl, setAudioUrl] = useState<string>("")

  useEffect(() => {
    const url = URL.createObjectURL(file)
    setAudioUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const updateTime = () => setCurrentTime(audio.currentTime)
    const updateDuration = () => setDuration(audio.duration)

    audio.addEventListener("timeupdate", updateTime)
    audio.addEventListener("loadedmetadata", updateDuration)
    audio.addEventListener("ended", () => setIsPlaying(false))

    return () => {
      audio.removeEventListener("timeupdate", updateTime)
      audio.removeEventListener("loadedmetadata", updateDuration)
      audio.removeEventListener("ended", () => setIsPlaying(false))
    }
  }, [audioUrl])

  const togglePlayPause = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      audio.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleSeek = (value: number[]) => {
    const audio = audioRef.current
    if (!audio) return

    audio.currentTime = value[0]
    setCurrentTime(value[0])
  }

  const handleVolumeChange = (value: number[]) => {
    const audio = audioRef.current
    if (!audio) return

    audio.volume = value[0] / 100
    setVolume(value)
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, "0")}`
  }

  const skip = (seconds: number) => {
    const audio = audioRef.current
    if (!audio) return

    audio.currentTime = Math.max(0, Math.min(duration, audio.currentTime + seconds))
  }

  const handleDownload = () => {
    const link = document.createElement("a")
    link.href = audioUrl
    link.download = title
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // Show success feedback
    const button = document.querySelector("[data-download-btn]") as HTMLElement
    if (button) {
      button.classList.add("success-pulse")
      setTimeout(() => button.classList.remove("success-pulse"), 1000)
    }
  }

  return (
    <Card className="border-border bg-card shadow-lg glow-green content-appear hover-lift transition-all duration-500">
      <CardHeader className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="grid-background h-full w-full" />
        </div>
        <CardTitle className="flex items-center justify-between relative z-10 mobile-stack mobile-text-sm">
          <div className="flex items-center gap-3 text-primary">
            <div className={`flex space-x-1 p-2 bg-primary/10 rounded-lg ${isPlaying ? "h-10" : ""}`}>
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1 bg-gradient-to-t from-primary to-accent rounded-full transition-all duration-300 ${
                    isPlaying ? "waveform-bar" : "h-2"
                  }`}
                />
              ))}
            </div>
            <span className="font-semibold">Audio Player</span>
          </div>
          {psnr && (
            <Badge
              variant={psnr > 40 ? "default" : psnr > 30 ? "secondary" : "destructive"}
              className={`bg-gradient-to-r from-green-500 to-green-600 text-white border-0 shadow-lg transition-all duration-300 ${
                psnr > 40 ? "glow-green animate-pulse" : ""
              }`}
            >
              <Activity className="h-3 w-3 mr-1" />
              PSNR: {psnr} dB
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 mobile-p-4">
        <audio ref={audioRef} src={audioUrl} />

        <div className="text-center p-4 bg-gradient-to-r from-primary/5 to-accent/5 rounded-xl">
          <h3 className="font-semibold text-foreground truncate text-lg">{title}</h3>
          <p className="text-sm text-muted-foreground font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </p>
        </div>

        <div className="space-y-2">
          <Slider
            value={[currentTime]}
            max={duration || 100}
            step={1}
            onValueChange={handleSeek}
            className="w-full [&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary [&_[role=slider]]:shadow-lg [&_[role=slider]]:hover:scale-110 [&_[role=slider]]:transition-transform"
          />
        </div>

        <div className="flex items-center justify-center space-x-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => skip(-10)}
            className="text-muted-foreground hover:text-primary hover:bg-primary/10 hover-lift transition-all duration-200"
          >
            <SkipBack className="h-5 w-5" />
          </Button>

          <Button
            onClick={togglePlayPause}
            size="lg"
            className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-full w-14 h-14 glow-green hover-lift transition-all duration-300 relative overflow-hidden"
          >
            <div className="absolute inset-0 shimmer opacity-30" />
            <div className="relative z-10">
              {isPlaying ? <Pause className="h-6 w-6" /> : <Play className="h-6 w-6 ml-0.5" />}
            </div>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => skip(10)}
            className="text-muted-foreground hover:text-primary hover:bg-primary/10 hover-lift transition-all duration-200"
          >
            <SkipForward className="h-5 w-5" />
          </Button>
        </div>

        <div className="flex items-center space-x-3 p-3 bg-secondary/50 rounded-lg">
          <Volume2 className="h-4 w-4 text-primary" />
          <Slider
            value={volume}
            max={100}
            step={1}
            onValueChange={handleVolumeChange}
            className="flex-1 [&_[role=slider]]:bg-primary [&_[role=slider]]:border-primary [&_[role=slider]]:hover:scale-110 [&_[role=slider]]:transition-transform"
          />
          <span className="text-xs text-muted-foreground w-10 font-mono">{volume[0]}%</span>
        </div>

        <Button
          onClick={handleDownload}
          data-download-btn
          className="btn-creative w-full mobile-full border-0 text-primary-foreground font-semibold transition-all duration-300 hover-lift"
        >
          <div className="flex items-center justify-center gap-2">
            <Download className="h-4 w-4" />
            <span>Download Processed Audio</span>
            <CheckCircle className="h-4 w-4 opacity-0 transition-opacity duration-300" />
          </div>
        </Button>
      </CardContent>
    </Card>
  )
}
