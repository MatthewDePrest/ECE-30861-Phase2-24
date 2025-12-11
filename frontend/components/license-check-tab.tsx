"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"

interface LicenseCheckTabProps {
  artifactId: string
}

export function LicenseCheckTab({ artifactId }: LicenseCheckTabProps) {
  const [githubUrl, setGithubUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<boolean | null>(null)

  const handleLicenseCheck = async () => {
    if (!githubUrl) return

    setLoading(true)
    try {
      // API call: POST /artifact/model/{id}/license-check
      const response = await fetch(`/api/artifact/model/${artifactId}/license-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_url: githubUrl }),
      })

      if (response.ok) {
        const data = await response.json()
        setResult(data.compatible)
      }
    } catch (error) {
      console.error("[v0] Failed to check license:", error)
      setResult(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">License Compatibility Check</h3>

      <div className="space-y-4">
        <div>
          <Label htmlFor="github-url" className="text-sm font-medium text-slate-700">
            GitHub Repository URL
          </Label>
          <div className="flex space-x-2 mt-1">
            <Input
              id="github-url"
              type="url"
              placeholder="https://github.com/..."
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              className="flex-1 focus:ring-2 focus:ring-blue-500"
              aria-describedby="github-url-help"
            />
            <Button
              onClick={handleLicenseCheck}
              disabled={!githubUrl || loading}
              className="bg-blue-500 hover:bg-blue-600 focus:ring-2 focus:ring-blue-500"
              aria-label="Check license compatibility"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
              <span className="ml-2">Check</span>
            </Button>
          </div>
          <p id="github-url-help" className="text-sm text-slate-500 mt-1">
            Check if this GitHub project's license is compatible with the model's license
          </p>
        </div>

        {/* Result Display */}
        {result !== null && (
          <Alert className={result ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"}>
            {result ? (
              <>
                <CheckCircle className="h-5 w-5 text-emerald-600" />
                <AlertTitle className="text-emerald-900">Compatible</AlertTitle>
                <AlertDescription className="text-emerald-700">
                  The licenses are compatible for fine-tuning and inference usage.
                </AlertDescription>
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5 text-red-600" />
                <AlertTitle className="text-red-900">Incompatible</AlertTitle>
                <AlertDescription className="text-red-700">
                  The licenses may not be compatible. Review license terms carefully.
                </AlertDescription>
              </>
            )}
          </Alert>
        )}
      </div>
    </Card>
  )
}
