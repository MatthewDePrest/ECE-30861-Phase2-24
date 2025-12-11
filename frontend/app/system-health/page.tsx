"use client"

import { useState, useEffect } from "react"
import { Activity, AlertCircle, CheckCircle, Clock, Server, Database, Zap, Loader2 } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Header } from "@/components/header"
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface HealthStatus {
  status: "healthy" | "degraded" | "down"
  uptime: number
  lastCheck: string
}

interface SystemMetrics {
  cpu: number[]
  memory: number[]
  requests: number[]
  responseTime: number[]
}

export default function SystemHealthPage() {
  const [health, setHealth] = useState<HealthStatus>({
    status: "healthy",
    uptime: 99.98,
    lastCheck: new Date().toISOString(),
  })
  const [loading, setLoading] = useState(true)

  // Mock metrics data
  const [metrics] = useState<SystemMetrics>({
    cpu: [45, 52, 48, 55, 49, 51, 47, 53, 50, 48, 52, 49],
    memory: [62, 65, 63, 68, 66, 64, 67, 65, 63, 66, 64, 65],
    requests: [120, 145, 132, 158, 142, 136, 148, 152, 138, 144, 150, 142],
    responseTime: [85, 92, 88, 95, 90, 87, 93, 89, 86, 91, 88, 90],
  })

  useEffect(() => {
    const fetchHealth = async () => {
      setLoading(true)
      try {
        // API call: GET /health
        const response = await fetch("/api/health")
        if (response.ok) {
          const data = await response.json()
          setHealth(data)
        }
      } catch (error) {
        console.error("[v0] Failed to fetch health status:", error)
      } finally {
        setLoading(false)
      }
    }

    // Mock data for demo
    setTimeout(() => setLoading(false), 500)
  }, [])

  const cpuData = metrics.cpu.map((value, index) => ({
    time: `${index}:00`,
    value,
  }))

  const memoryData = metrics.memory.map((value, index) => ({
    time: `${index}:00`,
    value,
  }))

  const requestsData = metrics.requests.map((value, index) => ({
    time: `${index}:00`,
    value,
  }))

  const responseTimeData = metrics.responseTime.map((value, index) => ({
    time: `${index}:00`,
    value,
  }))

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "text-emerald-600"
      case "degraded":
        return "text-amber-600"
      case "down":
        return "text-red-600"
      default:
        return "text-slate-600"
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
        return (
          <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">
            <CheckCircle className="h-3 w-3 mr-1" />
            Healthy
          </Badge>
        )
      case "degraded":
        return (
          <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">
            <AlertCircle className="h-3 w-3 mr-1" />
            Degraded
          </Badge>
        )
      case "down":
        return (
          <Badge className="bg-red-100 text-red-700 hover:bg-red-100">
            <AlertCircle className="h-3 w-3 mr-1" />
            Down
          </Badge>
        )
    }
  }

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

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-8">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-semibold text-slate-900 mb-2">System Health</h1>
            <p className="text-slate-500">Monitor system status and performance metrics</p>
          </div>

          {/* Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-slate-600">System Status</h3>
                <Activity className={`h-5 w-5 ${getStatusColor(health.status)}`} />
              </div>
              {getStatusBadge(health.status)}
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-slate-600">Uptime</h3>
                <Server className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{health.uptime}%</p>
              <p className="text-xs text-slate-500 mt-1">Last 30 days</p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-slate-600">Last Check</h3>
                <Clock className="h-5 w-5 text-slate-400" />
              </div>
              <p className="text-sm text-slate-900">{new Date(health.lastCheck).toLocaleString()}</p>
            </Card>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU Usage */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">CPU Usage</h3>
                  <p className="text-sm text-slate-500">Last 12 hours</p>
                </div>
                <Zap className="h-5 w-5 text-blue-600" />
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={cpuData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                    }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="#dbeafe" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>

            {/* Memory Usage */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Memory Usage</h3>
                  <p className="text-sm text-slate-500">Last 12 hours</p>
                </div>
                <Database className="h-5 w-5 text-blue-600" />
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={memoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                    }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#10b981" fill="#d1fae5" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>

            {/* API Requests */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">API Requests</h3>
                  <p className="text-sm text-slate-500">Requests per hour</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={requestsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                    }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Card>

            {/* Response Time */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Response Time</h3>
                  <p className="text-sm text-slate-500">Average (ms)</p>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={responseTimeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e2e8f0",
                      borderRadius: "8px",
                    }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
