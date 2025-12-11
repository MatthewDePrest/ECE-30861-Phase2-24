"use client"

import { useState } from "react"
import { Plus, Search, Eye, Pencil, Trash2, Bot, Database, Code } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useRouter } from "next/navigation"
import { Header } from "@/components/header"

// CHANGE: remove useToast import
// import { useToast } from "@/hooks/use-toast"

// CHANGE: add sonner import
import { toast } from "sonner"

type ArtifactType = "model" | "dataset" | "code"

interface Artifact {
  id: string
  name: string
  type: ArtifactType
  url?: string
}

export default function DashboardPage() {
  const router = useRouter()

  // CHANGE: removed toast destructuring
  // const { toast } = useToast()

  const [artifactType, setArtifactType] = useState<ArtifactType>("model")
  const [artifactUrl, setArtifactUrl] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [filterType, setFilterType] = useState("all")
  const [isRegistering, setIsRegistering] = useState(false)

  const [artifacts, setArtifacts] = useState<Artifact[]>([
    { id: "123456", name: "GPT-2 Model", type: "model", url: "https://huggingface.co/gpt2" },
    { id: "789012", name: "ImageNet Dataset", type: "dataset", url: "https://huggingface.co/datasets/imagenet" },
    { id: "345678", name: "Training Script", type: "code", url: "https://github.com/example/repo" },
  ])

  const handleRegister = async () => {
    if (!artifactUrl) {
      // CHANGE: use sonner
      toast.error("Please enter a source URL")
      return
    }

    setIsRegistering(true)
    try {
      const response = await fetch(`/api/artifact/${artifactType}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: artifactUrl }),
      })

      if (response.ok) {
        const newArtifact = await response.json()
        setArtifacts([newArtifact, ...artifacts])
        setArtifactUrl("")

        // CHANGE: use sonner
        toast.success("Artifact registered successfully")
      }
    } catch (error) {
      // CHANGE: use sonner
      toast.error("Failed to register artifact")
    } finally {
      setIsRegistering(false)
    }
  }

  const handleDelete = async (id: string, type: ArtifactType) => {
    try {
      await fetch(`/api/artifacts/${type}/${id}`, { method: "DELETE" })
      setArtifacts(artifacts.filter((a) => a.id !== id))

      // CHANGE: use sonner
      toast.success("Artifact deleted successfully")
    } catch (error) {
      // CHANGE: use sonner
      toast.error("Failed to delete artifact")
    }
  }

  const filteredArtifacts = artifacts.filter((artifact) => {
    const matchesSearch =
      artifact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      artifact.id.includes(searchQuery)
    const matchesType = filterType === "all" || artifact.type === filterType
    return matchesSearch && matchesType
  })

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-8">
          <Card className="p-6">
            <h2 className="text-2xl font-semibold text-slate-900 mb-6">Register New Artifact</h2>

            <div className="space-y-4">
              <div>
                <Label htmlFor="artifact-type" className="text-sm font-medium text-slate-700 mb-2 block">
                  Artifact Type
                </Label>
                <Tabs value={artifactType} onValueChange={(v) => setArtifactType(v as ArtifactType)}>
                  <TabsList className="grid w-full max-w-md grid-cols-3">
                    <TabsTrigger value="model">Model</TabsTrigger>
                    <TabsTrigger value="dataset">Dataset</TabsTrigger>
                    <TabsTrigger value="code">Code</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              <div>
                <Label htmlFor="artifact-url" className="text-sm font-medium text-slate-700">
                  Source URL
                </Label>
                <Input
                  id="artifact-url"
                  type="url"
                  placeholder="https://huggingface.co/..."
                  value={artifactUrl}
                  onChange={(e) => setArtifactUrl(e.target.value)}
                  className="w-full mt-1 focus:ring-2 focus:ring-blue-500"
                  aria-describedby="url-help"
                />
                <p id="url-help" className="text-sm text-slate-500 mt-1">
                  Supported: HuggingFace models/datasets, GitHub repos
                </p>
              </div>

              <Button
                className="w-full sm:w-auto bg-blue-500 hover:bg-blue-600 focus:ring-2 focus:ring-blue-500"
                onClick={handleRegister}
                disabled={isRegistering}
              >
                <Plus className="h-4 w-4 mr-2" />
                Register Artifact
              </Button>
            </div>
          </Card>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-slate-900">Your Artifacts</h2>
              <Badge variant="secondary" className="text-sm">
                {artifacts.length} total
              </Badge>
            </div>

            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                <Input
                  placeholder="Search by name or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 focus:ring-2 focus:ring-blue-500"
                  aria-label="Search artifacts"
                />
              </div>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-32 focus:ring-2 focus:ring-blue-500" aria-label="Filter by type">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="model">Models</SelectItem>
                  <SelectItem value="dataset">Datasets</SelectItem>
                  <SelectItem value="code">Code</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {filteredArtifacts.length === 0 ? (
                <Card className="p-12">
                  <div className="text-center">
                    <Database className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                    <p className="text-slate-500 mb-4">No artifacts found</p>
                    <Button variant="outline" onClick={() => setSearchQuery("")}>
                      Clear filters
                    </Button>
                  </div>
                </Card>
              ) : (
                filteredArtifacts.map((artifact) => (
                  <Card key={artifact.id} className="p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        <div className="p-2 bg-blue-50 rounded-lg">
                          {artifact.type === "model" && <Bot className="h-5 w-5 text-blue-600" />}
                          {artifact.type === "dataset" && <Database className="h-5 w-5 text-blue-600" />}
                          {artifact.type === "code" && <Code className="h-5 w-5 text-blue-600" />}
                        </div>

                        <div>
                          <h3 className="font-semibold text-slate-900">{artifact.name}</h3>
                          <p className="text-sm text-slate-500 font-mono">ID: {artifact.id}</p>
                          <Badge variant="outline" className="mt-1">
                            {artifact.type}
                          </Badge>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label="View artifact details"
                          className="focus:ring-2 focus:ring-blue-500"
                          onClick={() => router.push(`/model-details?id=${artifact.id}&type=${artifact.type}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label="Edit artifact"
                          className="focus:ring-2 focus:ring-blue-500"
                          onClick={() => {
                            // CHANGE: use sonner
                            toast.info("Edit functionality coming soon")
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label="Delete artifact"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 focus:ring-2 focus:ring-red-500"
                          onClick={() => handleDelete(artifact.id, artifact.type)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
