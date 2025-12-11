"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { GitBranch, Database, ArrowDown } from "lucide-react"

interface LineageNode {
  artifact_id: string
  name: string
  source: string
}

interface LineageEdge {
  from_node_artifact_id: string
  to_node_artifact_id: string
  relationship: string
}

interface LineageData {
  nodes: LineageNode[]
  edges: LineageEdge[]
}

interface LineageTabProps {
  artifactId: string
}

export function LineageTab({ artifactId }: LineageTabProps) {
  const [lineage, setLineage] = useState<LineageData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchLineage = async () => {
      setLoading(true)
      try {
        // API call: GET /artifact/model/{id}/lineage
        const response = await fetch(`/api/artifact/model/${artifactId}/lineage`)
        if (response.ok) {
          const data = await response.json()
          setLineage(data)
        }
      } catch (error) {
        console.error("[v0] Failed to fetch lineage:", error)
      } finally {
        setLoading(false)
      }
    }

    // Mock data for demo
    setLineage({
      nodes: [
        { artifact_id: artifactId, name: "GPT-2 Model", source: "HuggingFace" },
        { artifact_id: "base_model_123", name: "Base Transformer", source: "Training" },
        { artifact_id: "dataset_456", name: "Training Dataset", source: "Collection" },
      ],
      edges: [
        { from_node_artifact_id: "base_model_123", to_node_artifact_id: artifactId, relationship: "fine-tuned" },
        { from_node_artifact_id: "dataset_456", to_node_artifact_id: artifactId, relationship: "trained-with" },
      ],
    })
    setLoading(false)
  }, [artifactId])

  if (loading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Model Lineage Graph</h3>
        <Skeleton className="h-64 w-full" />
      </Card>
    )
  }

  if (lineage.nodes.length === 0) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Model Lineage Graph</h3>
        <div className="text-center py-12">
          <GitBranch className="h-12 w-12 mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500">No lineage data available</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">Model Lineage Graph</h3>

      <div className="space-y-6">
        {/* Simple Tree Visualization */}
        <div className="border border-slate-200 rounded-lg p-6 bg-slate-50">
          {lineage.nodes.map((node) => (
            <div key={node.artifact_id} className="mb-4 last:mb-0">
              <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-slate-200">
                <Database className="h-5 w-5 text-blue-600" />
                <div className="flex-1">
                  <p className="font-medium text-slate-900">{node.name}</p>
                  <p className="text-xs text-slate-500 font-mono">{node.artifact_id}</p>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {node.source}
                  </Badge>
                </div>
              </div>

              {/* Show edges */}
              {lineage.edges
                .filter((e) => e.from_node_artifact_id === node.artifact_id)
                .map((edge) => (
                  <div key={edge.to_node_artifact_id} className="ml-8 mt-2 flex items-center space-x-2">
                    <ArrowDown className="h-4 w-4 text-slate-400" />
                    <span className="text-sm text-slate-600">{edge.relationship}</span>
                  </div>
                ))}
            </div>
          ))}
        </div>

        {/* Metadata Table */}
        <div>
          <h4 className="font-medium text-slate-900 mb-2">Nodes</h4>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Artifact ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Source</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lineage.nodes.map((node) => (
                  <TableRow key={node.artifact_id}>
                    <TableCell className="font-mono text-sm">{node.artifact_id}</TableCell>
                    <TableCell>{node.name}</TableCell>
                    <TableCell>{node.source}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </Card>
  )
}
