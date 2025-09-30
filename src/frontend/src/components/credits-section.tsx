"use client"

import { Github, Linkedin, Mail } from "lucide-react"

export function CreditsSection() {
  const developers = [
    {
      name: "Alex Chen",
      role: "Full-Stack Developer & Cryptography Specialist",
      image: "/professional-developer-portrait-asian-male.jpg",
      bio: "Specialized in cryptographic algorithms and secure web applications. Passionate about digital privacy and steganography techniques.",
      github: "alexchen-crypto",
      linkedin: "alex-chen-dev",
      email: "alex.chen@example.com",
    },
    {
      name: "Sarah Rodriguez",
      role: "Audio Processing Engineer & UI/UX Designer",
      image: "/professional-developer-portrait-latina-female.jpg",
      bio: "Expert in digital signal processing and modern web interfaces. Focused on creating intuitive tools for complex audio manipulation.",
      github: "sarah-audio-dev",
      linkedin: "sarah-rodriguez-eng",
      email: "sarah.rodriguez@example.com",
    },
  ]

  return (
    <section className="py-16 bg-gradient-to-br from-green-50/50 to-emerald-50/30 rounded-3xl border border-green-100/50">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-green-900 mb-4">Meet the Developers</h2>
          <div className="w-24 h-1 bg-gradient-to-r from-green-500 to-emerald-500 mx-auto rounded-full mb-8"></div>

          <div className="max-w-4xl mx-auto">
            <p className="text-lg text-green-800 leading-relaxed mb-6">
              We created this audio steganography web application as part of our Cryptography course at Institut
              Teknologi Bandung. Our goal was to make advanced steganographic techniques accessible through an
              intuitive, modern interface that combines security with usability.
            </p>
            <p className="text-green-700">
              This project demonstrates how hidden messages can be securely embedded within audio files using
              multiple-LSB techniques, while maintaining audio quality and providing robust encryption options. We
              believe in making cryptographic tools user-friendly without compromising on security standards.
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {developers.map((dev, index) => (
            <div
              key={dev.name}
              className="group bg-white/70 backdrop-blur-sm rounded-2xl p-6 border border-green-100/50 hover:border-green-200 transition-all duration-300 hover:shadow-lg hover:shadow-green-100/50 hover:-translate-y-1"
            >
              <div className="flex flex-col items-center text-center">
                <div className="relative mb-4">
                  <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-green-200 group-hover:border-green-300 transition-colors duration-300">
                    <img
                      src={dev.image || "/placeholder.svg"}
                      alt={dev.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                    />
                  </div>
                  <div className="absolute -bottom-2 -right-2 w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                  </div>
                </div>

                <h3 className="text-xl font-bold text-green-900 mb-1">{dev.name}</h3>
                <p className="text-green-600 font-medium mb-3">{dev.role}</p>
                <p className="text-sm text-green-700 mb-4 leading-relaxed">{dev.bio}</p>

                <div className="flex space-x-3">
                  <a
                    href={`https://github.com/${dev.github}`}
                    className="p-2 rounded-full bg-green-100 hover:bg-green-200 text-green-700 hover:text-green-800 transition-all duration-200 hover:scale-110"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Github className="h-4 w-4" />
                  </a>
                  <a
                    href={`https://linkedin.com/in/${dev.linkedin}`}
                    className="p-2 rounded-full bg-green-100 hover:bg-green-200 text-green-700 hover:text-green-800 transition-all duration-200 hover:scale-110"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Linkedin className="h-4 w-4" />
                  </a>
                  <a
                    href={`mailto:${dev.email}`}
                    className="p-2 rounded-full bg-green-100 hover:bg-green-200 text-green-700 hover:text-green-800 transition-all duration-200 hover:scale-110"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Mail className="h-4 w-4" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-12">
          <div className="inline-flex items-center space-x-2 text-green-600">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">Institut Teknologi Bandung - Cryptography Course 2025</span>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>
    </section>
  )
}
