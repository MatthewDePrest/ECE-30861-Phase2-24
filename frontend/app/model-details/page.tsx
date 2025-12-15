"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, Bot, Database, Code, Loader2, TrendingUp, Zap, Shield, HardDrive } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

const BASE_URL = "https://q53b6eic4m.execute-api.us-east-1.amazonaws.com/prod"

interface Artifact {
  metadata: {
    id: string
    name: string
    type: "model" | "dataset" | "code"
  }
  data: {
    url: string
    download_url?: string
  }
}

interface SizeScore {
  raspberry_pi: number
  jetson_nano: number
  desktop_pc: number
  aws_server: number
}

interface ModelRating {
  name: string
  category: string
  net_score: number
  ramp_up_time: number
  bus_factor: number
  performance_claims: number
  license: number
  dataset_and_code_score: number
  dataset_quality: number
  code_quality: number
  size_score: SizeScore
}

function Header() {
  return (
    <header className="border-b bg-white">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <h1 className="text-xl font-semibold text-slate-900">ML Artifact Registry</h1>
      </div>
    </header>
  )
}

function ModelDetailsContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const artifactId = searchParams.get("id")
  const artifactType = searchParams.get("type") as "model" | "dataset" | "code"

  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [rating, setRating] = useState<ModelRating | null>(null)
  const [loading, setLoading] = useState(true)
  const [ratingLoading, setRatingLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchArtifact = async () => {
      if (!artifactId || !artifactType) {
        setError("Missing artifact ID or type")
        setLoading(false)
        return
      }

      setLoading(true)
      setError(null)

      try {
        const response = await fetch(`${BASE_URL}/artifacts/${artifactType}/${artifactId}`)
        
        if (!response.ok) {
          throw new Error(`Failed to fetch artifact: ${response.status}`)
        }

        const data = await response.json()
        setArtifact(data)

        // Fetch rating only for models
        if (artifactType === "model") {
          setRatingLoading(true)
          try {
            const ratingResponse = await fetch(`${BASE_URL}/artifact/model/${artifactId}/rate`)
            if (ratingResponse.ok) {
              const ratingData = await ratingResponse.json()
              setRating(ratingData)
            }
          } catch (err) {
            console.error("Failed to fetch rating:", err)
          } finally {
            setRatingLoading(false)
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load artifact")
        console.error("Failed to fetch artifact:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchArtifact()
  }, [artifactId, artifactType])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-7xl mx-auto px-6 py-8 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      </div>
    )
  }

  if (error || !artifact) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-7xl mx-auto px-6 py-8">
          <Card className="p-6">
            <p className="text-red-600">{error || "Artifact not found"}</p>
            <Button onClick={() => router.back()} className="mt-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Card>
        </div>
      </div>
    )
  }

  const getIcon = () => {
    switch (artifact.metadata.type) {
      case "model":
        return <Bot className="h-8 w-8 text-blue-600" />
      case "dataset":
        return <Database className="h-8 w-8 text-blue-600" />
      case "code":
        return <Code className="h-8 w-8 text-blue-600" />
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-green-600"
    if (score >= 0.5) return "text-yellow-600"
    return "text-red-600"
  }

  const formatScore = (score: number) => {
    if (score === -1) return "N/A"
    return (score * 100).toFixed(0) + "%"
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-6">
          <Button variant="ghost" onClick={() => router.back()} className="focus:ring-2 focus:ring-blue-500">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>

          <Card className="p-6">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-blue-50 rounded-xl">{getIcon()}</div>
              <div className="flex-1">
                <h1 className="text-3xl font-semibold text-slate-900">{artifact.metadata.name}</h1>
                <div className="flex items-center gap-3 mt-2">
                  <Badge variant="secondary" className="font-mono">
                    {artifact.metadata.id}
                  </Badge>
                  <Badge>{artifact.metadata.type}</Badge>
                </div>
              </div>
            </div>
          </Card>

          {artifact.metadata.type === "model" && (
            <>
              {ratingLoading ? (
                <Card className="p-6">
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                    <span className="ml-2 text-slate-600">Loading ratings...</span>
                  </div>
                </Card>
              ) : rating ? (
                <>
                  <Card className="p-6">
                    <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center">
                      <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
                      Model Ratings
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Net Score</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.net_score)}`}>
                              {formatScore(rating.net_score)}
                            </span>
                          </div>
                          <Progress value={rating.net_score * 100} className="h-2" />
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Ramp-Up Time</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.ramp_up_time)}`}>
                              {formatScore(rating.ramp_up_time)}
                            </span>
                          </div>
                          <Progress value={rating.ramp_up_time * 100} className="h-2" />
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Bus Factor</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.bus_factor)}`}>
                              {formatScore(rating.bus_factor)}
                            </span>
                          </div>
                          <Progress value={rating.bus_factor * 100} className="h-2" />
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Performance Claims</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.performance_claims)}`}>
                              {formatScore(rating.performance_claims)}
                            </span>
                          </div>
                          <Progress value={rating.performance_claims * 100} className="h-2" />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">License</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.license)}`}>
                              {formatScore(rating.license)}
                            </span>
                          </div>
                          <Progress value={rating.license * 100} className="h-2" />
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Dataset & Code</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.dataset_and_code_score)}`}>
                              {formatScore(rating.dataset_and_code_score)}
                            </span>
                          </div>
                          <Progress value={rating.dataset_and_code_score * 100} className="h-2" />
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Dataset Quality</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.dataset_quality)}`}>
                              {formatScore(rating.dataset_quality)}
                            </span>
                          </div>
                          <Progress value={rating.dataset_quality * 100} className="h-2" />
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <span className="text-sm font-medium text-slate-700">Code Quality</span>
                            <span className={`text-sm font-semibold ${getScoreColor(rating.code_quality)}`}>
                              {formatScore(rating.code_quality)}
                            </span>
                          </div>
                          <Progress value={rating.code_quality * 100} className="h-2" />
                        </div>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-6">
                    <h2 className="text-xl font-semibold text-slate-900 mb-4 flex items-center">
                      <HardDrive className="h-5 w-5 mr-2 text-blue-600" />
                      Deployment Size Scores
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-sm text-slate-600 mb-2">Raspberry Pi</div>
                        <div className={`text-2xl font-bold ${getScoreColor(rating.size_score.raspberry_pi)}`}>
                          {formatScore(rating.size_score.raspberry_pi)}
                        </div>
                      </div>

                      <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-sm text-slate-600 mb-2">Jetson Nano</div>
                        <div className={`text-2xl font-bold ${getScoreColor(rating.size_score.jetson_nano)}`}>
                          {formatScore(rating.size_score.jetson_nano)}
                        </div>
                      </div>

                      <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-sm text-slate-600 mb-2">Desktop PC</div>
                        <div className={`text-2xl font-bold ${getScoreColor(rating.size_score.desktop_pc)}`}>
                          {formatScore(rating.size_score.desktop_pc)}
                        </div>
                      </div>

                      <div className="bg-slate-50 rounded-lg p-4">
                        <div className="text-sm text-slate-600 mb-2">AWS Server</div>
                        <div className={`text-2xl font-bold ${getScoreColor(rating.size_score.aws_server)}`}>
                          {formatScore(rating.size_score.aws_server)}
                        </div>
                      </div>
                    </div>
                  </Card>
                </>
              ) : (
                <Card className="p-6">
                  <p className="text-slate-500">No rating data available for this model</p>
                </Card>
              )}
            </>
          )}

          {artifact.metadata.type !== "model" && (
            <Card className="p-6">
              <p className="text-slate-500">
                Detailed metrics are only available for model artifacts.
              </p>
            </Card>
          )}
        </div>
      </main>
    </div>
  )
}

export default function ModelDetailsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50">
          <Header />
          <div className="max-w-7xl mx-auto px-6 py-8 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        </div>
      }
    >
      <ModelDetailsContent />
    </Suspense>
  )
}

// function Progress({ value, className }: { value: number; className?: string }) {
//   return (
//     <div className={`bg-slate-200 rounded-full overflow-hidden ${className}`}>
//       <div
//         className="bg-blue-600 h-full transition-all duration-300"
//         style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
//       />
//     </div>
//   )
// }