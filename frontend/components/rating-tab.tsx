"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Cpu, Monitor, Server } from "lucide-react"
import { cn } from "@/lib/utils"

interface RatingData {
  net_score: number
  net_score_latency: number
  ramp_up_time: number
  ramp_up_time_latency: number
  bus_factor: number
  bus_factor_latency: number
  reproducibility: number
  reproducibility_latency: number
  correctness: number
  correctness_latency: number
  responsiveness: number
  responsiveness_latency: number
  license_score: number
  license_score_latency: number
  size_score: {
    raspberry_pi: number
    jetson_nano: number
    desktop_pc: number
    aws_server: number
  }
}

interface RatingTabProps {
  artifactId: string
}

export function RatingTab({ artifactId }: RatingTabProps) {
  const [rating, setRating] = useState<RatingData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRating = async () => {
      setLoading(true)
      try {
        // API call: GET /artifact/model/{id}/rate
        const response = await fetch(`/api/artifact/model/${artifactId}/rate`)
        if (response.ok) {
          const data = await response.json()
          setRating(data)
        }
      } catch (error) {
        console.error("[v0] Failed to fetch rating:", error)
      } finally {
        setLoading(false)
      }
    }

    // Mock data for demo
    setRating({
      net_score: 0.85,
      net_score_latency: 1.2,
      ramp_up_time: 0.72,
      ramp_up_time_latency: 0.8,
      bus_factor: 0.68,
      bus_factor_latency: 0.9,
      reproducibility: 0.91,
      reproducibility_latency: 1.1,
      correctness: 0.88,
      correctness_latency: 1.5,
      responsiveness: 0.79,
      responsiveness_latency: 0.7,
      license_score: 0.95,
      license_score_latency: 0.5,
      size_score: {
        raspberry_pi: 0.45,
        jetson_nano: 0.68,
        desktop_pc: 0.89,
        aws_server: 0.96,
      },
    })
    setLoading(false)
  }, [artifactId])

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Model Rating Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </Card>
      </div>
    )
  }

  if (!rating) {
    return <div className="text-slate-500">Failed to load rating data</div>
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Model Rating Metrics</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard label="Net Score" value={rating.net_score} latency={rating.net_score_latency} />
          <MetricCard label="Ramp Up Time" value={rating.ramp_up_time} latency={rating.ramp_up_time_latency} />
          <MetricCard label="Bus Factor" value={rating.bus_factor} latency={rating.bus_factor_latency} />
          <MetricCard label="Reproducibility" value={rating.reproducibility} latency={rating.reproducibility_latency} />
          <MetricCard label="Correctness" value={rating.correctness} latency={rating.correctness_latency} />
          <MetricCard label="Responsiveness" value={rating.responsiveness} latency={rating.responsiveness_latency} />
          <MetricCard label="License Score" value={rating.license_score} latency={rating.license_score_latency} />
        </div>
      </Card>

      {/* Size Scores Card */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Deployment Size Scores</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SizeScoreCard label="Raspberry Pi" score={rating.size_score.raspberry_pi} icon={<Cpu />} />
          <SizeScoreCard label="Jetson Nano" score={rating.size_score.jetson_nano} icon={<Cpu />} />
          <SizeScoreCard label="Desktop PC" score={rating.size_score.desktop_pc} icon={<Monitor />} />
          <SizeScoreCard label="AWS Server" score={rating.size_score.aws_server} icon={<Server />} />
        </div>
      </Card>
    </div>
  )
}

function MetricCard({ label, value, latency }: { label: string; value: number; latency: number }) {
  return (
    <div className="p-4 border border-slate-200 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-600">{label}</span>
        <span className="text-xs text-slate-400">{latency.toFixed(2)}s</span>
      </div>
      <div className="text-2xl font-bold text-slate-900">{value.toFixed(2)}</div>
      <Progress
        value={value * 100}
        className={cn(
          "mt-2",
          value >= 0.7 && "[&>div]:bg-emerald-500",
          value < 0.7 && value >= 0.4 && "[&>div]:bg-amber-500",
          value < 0.4 && "[&>div]:bg-red-500",
        )}
      />
    </div>
  )
}

function SizeScoreCard({ label, score, icon }: { label: string; score: number; icon: React.ReactNode }) {
  return (
    <div className="p-4 border border-slate-200 rounded-lg text-center">
      <div className="flex justify-center mb-2 text-blue-600">{icon}</div>
      <p className="text-xs text-slate-600 mb-2">{label}</p>
      <p className="text-xl font-bold text-slate-900">{score.toFixed(2)}</p>
      <Progress value={score * 100} className="mt-2" />
    </div>
  )
}
