"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { ArrowLeft, Bot, Database, Code, ExternalLink, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Header } from "@/components/header"
import { RatingTab } from "@/components/rating-tab"
import { CostTab } from "@/components/cost-tab"
import { LineageTab } from "@/components/lineage-tab"
import { LicenseCheckTab } from "@/components/license-check-tab"

interface Artifact {
  id: string
  name: string
  type: "model" | "dataset" | "code"
  url?: string
}

function ModelDetailsContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const artifactId = searchParams.get("id")
  const artifactType = searchParams.get("type") as "model" | "dataset" | "code"

  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchArtifact = async () => {
      if (!artifactId || !artifactType) return

      setLoading(true)
      try {
        // API call: GET /artifacts/{artifact_type}/{id}
        const response = await fetch(`/api/artifacts/${artifactType}/${artifactId}`)
        if (response.ok) {
          const data = await response.json()
          setArtifact(data)
        }
      } catch (error) {
        console.error("[v0] Failed to fetch artifact:", error)
      } finally {
        setLoading(false)
      }
    }

    // Mock data for demo
    setArtifact({
      id: artifactId || "123456",
      name: "GPT-2 Model",
      type: artifactType || "model",
      url: "https://huggingface.co/gpt2",
    })
    setLoading(false)
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

  if (!artifact) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />
        <div className="max-w-7xl mx-auto px-6 py-8">
          <p className="text-slate-500">Artifact not found</p>
        </div>
      </div>
    )
  }

  const getIcon = () => {
    switch (artifact.type) {
      case "model":
        return <Bot className="h-8 w-8 text-blue-600" />
      case "dataset":
        return <Database className="h-8 w-8 text-blue-600" />
      case "code":
        return <Code className="h-8 w-8 text-blue-600" />
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-6">
          {/* Back Button */}
          <Button variant="ghost" onClick={() => router.back()} className="focus:ring-2 focus:ring-blue-500">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>

          {/* Model Header */}
          <Card className="p-6">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-blue-50 rounded-xl">{getIcon()}</div>
              <div className="flex-1">
                <h1 className="text-3xl font-semibold text-slate-900">{artifact.name}</h1>
                <div className="flex items-center gap-3 mt-2">
                  <Badge variant="secondary" className="font-mono">
                    {artifact.id}
                  </Badge>
                  <Badge>{artifact.type}</Badge>
                </div>
                {artifact.url && (
                  <a
                    href={artifact.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline mt-2 inline-flex items-center focus:ring-2 focus:ring-blue-500 rounded"
                  >
                    View Source <ExternalLink className="h-3 w-3 ml-1" />
                  </a>
                )}
              </div>
            </div>
          </Card>

          {/* Operations Tabs */}
          <Tabs defaultValue="rating" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="rating">Rating</TabsTrigger>
              <TabsTrigger value="cost">Cost Analysis</TabsTrigger>
              <TabsTrigger value="lineage">Lineage</TabsTrigger>
              <TabsTrigger value="license">License Check</TabsTrigger>
            </TabsList>

            <TabsContent value="rating">
              <RatingTab artifactId={artifact.id} />
            </TabsContent>

            <TabsContent value="cost">
              <CostTab artifactId={artifact.id} artifactType={artifact.type} />
            </TabsContent>

            <TabsContent value="lineage">
              <LineageTab artifactId={artifact.id} />
            </TabsContent>

            <TabsContent value="license">
              <LicenseCheckTab artifactId={artifact.id} />
            </TabsContent>
          </Tabs>
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
