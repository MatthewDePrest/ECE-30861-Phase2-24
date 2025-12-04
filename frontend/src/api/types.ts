export type ArtifactType = 'model' | 'dataset' | 'code'

export interface ArtifactMetadata {
  id: string
  name: string
  type: ArtifactType
}

export interface ArtifactData {
  url: string
  download_url?: string
}

export interface Artifact {
  metadata: ArtifactMetadata
  data: ArtifactData
}

export interface ModelRatingEntry { metric: string; value: number; latencyMs?: number }
export interface ModelRating { id: string; metrics: ModelRatingEntry[] }

export type ArtifactCost = Record<string, any>

export type AuthenticationRequest = { user: { name: string; is_admin: boolean }; secret: { password: string } }

export type ArtifactQuery = { name?: string }

export interface HealthComponent { name: string; status: 'ok'|'degraded'|'critical'|'unknown' }

export interface HealthComponentCollection { components: HealthComponent[] }
