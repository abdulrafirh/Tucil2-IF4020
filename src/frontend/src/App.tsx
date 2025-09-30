import './App.css';
import { useState } from "react"
import { Header } from "@/components/header"
import { HeroSection } from "@/components/hero-section"
import { EmbedSection } from "@/components/embed-section"
import { ExtractSection } from "@/components/extract-section"
import { AudioPlayer } from "@/components/audio-player"
import { ResultsPanel } from "@/components/results-panel"
import { Music } from "lucide-react"
import { CreditsSection } from "@/components/credits-section"

export default function Home() {
  const [activeTab, setActiveTab] = useState<"embed" | "extract">("embed")
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [secretFile, setSecretFile] = useState<File | null>(null)
  const [results, setResults] = useState<any>(null)
  const [processedAudio, setProcessedAudio] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleProcessingStart = () => {
    setIsProcessing(true)
    setResults(null)
    setProcessedAudio(null)
  }

  const handleResults = (newResults: any) => {
    setResults(newResults)
    setIsProcessing(false)
    if (newResults.success && audioFile) {
      const processedFile = new File([audioFile], `stego_${audioFile.name}`, {
        type: audioFile.type,
      })
      setProcessedAudio(processedFile)
    }
  }

  return (
    <div className="min-h-screen bg-background dots-background">
      <Header />

      <main className="container mx-auto px-4 py-8 space-y-12">
        <HeroSection />

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div
              className={`tab-slider ${activeTab === "extract" ? 'data-[active="extract"]' : ""}`}
              data-active={activeTab}
            >
              <div className="flex">
                <button
                  onClick={() => setActiveTab("embed")}
                  className={`tab-button ${activeTab === "embed" ? "active" : ""}`}
                >
                  Embed Message
                </button>
                <button
                  onClick={() => setActiveTab("extract")}
                  className={`tab-button ${activeTab === "extract" ? "active" : ""}`}
                >
                  Extract Message
                </button>
              </div>
            </div>

            {/* Content Sections */}
            {activeTab === "embed" ? (
              <EmbedSection
                audioFile={audioFile}
                setAudioFile={setAudioFile}
                secretFile={secretFile}
                setSecretFile={setSecretFile}
                onResults={handleResults}
                onProcessingStart={handleProcessingStart}
                isProcessing={isProcessing}
              />
            ) : (
              <ExtractSection
                audioFile={audioFile}
                setAudioFile={setAudioFile}
                onResults={handleResults}
                onProcessingStart={handleProcessingStart}
                isProcessing={isProcessing}
              />
            )}
          </div>

          <div className="space-y-6">
            {processedAudio && results?.success ? (
              <div className="content-appear">
                <AudioPlayer file={processedAudio} title={processedAudio.name} psnr={results.psnr} />
              </div>
            ) : (
              <div className="audio-placeholder rounded-xl">
                <div className="audio-placeholder-content">
                  <Music className="h-12 w-12 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Audio Player</h3>
                  <p className="text-sm text-center max-w-xs">
                    Your processed audio will appear here after embedding or extraction
                  </p>
                </div>
              </div>
            )}

            {(isProcessing || results) && (
              <div className="content-appear">
                <ResultsPanel results={results} isProcessing={isProcessing} />
              </div>
            )}
          </div>
        </div>

        <CreditsSection />
      </main>
    </div>
  )
}
