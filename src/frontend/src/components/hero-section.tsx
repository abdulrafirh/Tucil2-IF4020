import { Shield, Lock, Music, Zap } from "lucide-react"

export function HeroSection() {
  return (
    <section className="text-center py-12 space-y-8">
      <div className="space-y-4">
        <h1 className="text-4xl md:text-6xl font-bold text-balance">
          Advanced Audio <span className="text-primary">Steganography</span>
        </h1>
        <p className="text-xl text-muted-foreground text-balance max-w-2xl mx-auto">
          Hide secret messages in MP3 audio files using multiple-LSB encoding with military-grade encryption
        </p>
      </div>

      <div className="grid md:grid-cols-4 gap-6 max-w-4xl mx-auto">
        <div className="p-6 bg-card rounded-lg border border-border shadow-sm hover:border-primary/50 transition-colors">
          <div className="p-3 bg-primary/10 rounded-lg w-fit mx-auto mb-4">
            <Shield className="h-6 w-6 text-primary" />
          </div>
          <h3 className="font-semibold mb-2">Multiple-LSB</h3>
          <p className="text-sm text-muted-foreground">1-4 bit LSB encoding for optimal capacity</p>
        </div>

        <div className="p-6 bg-card rounded-lg border border-border shadow-sm hover:border-primary/50 transition-colors">
          <div className="p-3 bg-primary/10 rounded-lg w-fit mx-auto mb-4">
            <Lock className="h-6 w-6 text-primary" />
          </div>
          <h3 className="font-semibold mb-2">Vigenère Cipher</h3>
          <p className="text-sm text-muted-foreground">Extended 256-character encryption</p>
        </div>

        <div className="p-6 bg-card rounded-lg border border-border shadow-sm hover:border-primary/50 transition-colors">
          <div className="p-3 bg-primary/10 rounded-lg w-fit mx-auto mb-4">
            <Music className="h-6 w-6 text-primary" />
          </div>
          <h3 className="font-semibold mb-2">MP3 Support</h3>
          <p className="text-sm text-muted-foreground">Mono & stereo audio processing</p>
        </div>

        <div className="p-6 bg-card rounded-lg border border-border shadow-sm hover:border-primary/50 transition-colors">
          <div className="p-3 bg-primary/10 rounded-lg w-fit mx-auto mb-4">
            <Zap className="h-6 w-6 text-primary" />
          </div>
          <h3 className="font-semibold mb-2">PSNR Analysis</h3>
          <p className="text-sm text-muted-foreground">Quality metrics & validation</p>
        </div>
      </div>
    </section>
  )
}
