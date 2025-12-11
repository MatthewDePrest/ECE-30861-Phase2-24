"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"

interface CostData {
  [artifactId: string]: {
    total_cost: number
    standalone_cost?: number
  }
}

interface CostTabProps {
  artifactId: string
  artifactType: string
}

export function CostTab({ artifactId, artifactType }: CostTabProps) {
  const [costData, setCostData] = useState<CostData>({})
  const [includeDeps, setIncludeDeps] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCost = async () => {
      setLoading(true)
      try {
        // API call: GET /artifact/{artifact_type}/{id}/cost?dependency={true|false}
        const response = await fetch(`/api/artifact/${artifactType}/${artifactId}/cost?dependency=${includeDeps}`)
        if (response.ok) {
          const data = await response.json()
          setCostData(data)
        }
      } catch (error) {
        console.error("[v0] Failed to fetch cost:", error)
      } finally {
        setLoading(false)
      }
    }

    // Mock data for demo
    if (includeDeps) {
      setCostData({
        [artifactId]: { total_cost: 542.3, standalone_cost: 245.8 },
        dep_1: { total_cost: 156.2 },
        dep_2: { total_cost: 98.5 },
        dep_3: { total_cost: 41.8 },
      })
    } else {
      setCostData({
        [artifactId]: { total_cost: 245.8 },
      })
    }
    setLoading(false)
  }, [artifactId, artifactType, includeDeps])

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Cost Analysis</h3>
        <div className="flex items-center space-x-2">
          <Label htmlFor="include-deps" className="text-sm text-slate-600">
            Include Dependencies
          </Label>
          <Switch
            id="include-deps"
            checked={includeDeps}
            onCheckedChange={setIncludeDeps}
            aria-label="Toggle dependency inclusion"
          />
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-32 w-full" />
      ) : (
        <div className="space-y-6">
          {/* Total Cost */}
          <div className="text-center p-6 bg-blue-50 rounded-lg">
            <p className="text-sm text-slate-600 mb-1">Total Cost</p>
            <p className="text-4xl font-bold text-blue-600">
              {costData[artifactId]?.total_cost.toFixed(1) || 0} <span className="text-xl font-normal">MB</span>
            </p>
          </div>

          {/* Dependency Breakdown */}
          {includeDeps && Object.keys(costData).length > 1 && (
            <div>
              <h4 className="font-medium text-slate-900 mb-3">Dependency Breakdown</h4>
              <div className="space-y-2">
                {Object.entries(costData).map(([id, data]) => (
                  <div key={id} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
                    <span className="text-sm font-mono text-slate-700">{id}</span>
                    <div className="text-right">
                      {data.standalone_cost !== undefined && (
                        <p className="text-xs text-slate-500">Standalone: {data.standalone_cost.toFixed(1)} MB</p>
                      )}
                      <p className="font-semibold text-slate-900">Total: {data.total_cost.toFixed(1)} MB</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
