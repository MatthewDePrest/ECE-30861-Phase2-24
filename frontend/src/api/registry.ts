import client from './client'
import type * as T from './types'

function readOffset(resp: any){
  const offset = resp?.headers?.offset || resp?.headers?.Offset || undefined
  return offset
}

export async function authenticate(req: T.AuthenticationRequest): Promise<string>{
  const r = await client.put('/authenticate', req)
  const token = r.data as string
  if (token) localStorage.setItem('token', token)
  return token
}

export async function listArtifacts(queries: T.ArtifactQuery[], offset?: string){
  const headers: any = {}
  if (offset) headers['offset'] = offset
  const r = await client.post('/artifacts', queries, { headers })
  const next = readOffset(r)
  return { items: r.data as T.ArtifactMetadata[], nextOffset: next }
}

export async function createArtifact(type: T.ArtifactType, body: { url: string }): Promise<T.Artifact>{
  const r = await client.post(`/artifact/${type}`, body)
  return r.data as T.Artifact
}

export async function getArtifact(type: T.ArtifactType, id: string): Promise<T.Artifact>{
  const r = await client.get(`/artifacts/${type}/${id}`)
  return r.data as T.Artifact
}

export async function updateArtifact(type: T.ArtifactType, id: string, body: { url: string }): Promise<void>{
  await client.put(`/artifacts/${type}/${id}`, body)
}

export async function deleteArtifact(type: T.ArtifactType, id: string): Promise<void>{
  await client.delete(`/artifacts/${type}/${id}`)
}

export async function byName(name: string){
  const r = await client.get(`/artifact/byName/${encodeURIComponent(name)}`)
  return r.data as T.ArtifactMetadata[]
}

export async function byRegex(regex: string){
  const r = await client.post(`/artifact/byRegEx`, { regex })
  return r.data as T.ArtifactMetadata[]
}

export async function modelRate(id: string): Promise<T.ModelRating>{
  const r = await client.get(`/artifact/model/${id}/rate`)
  return r.data as T.ModelRating
}

export async function artifactCost(type: T.ArtifactType, id: string, dependency = false): Promise<T.ArtifactCost>{
  const r = await client.get(`/artifact/${type}/${id}/cost`, { params: { dependency } })
  return r.data as T.ArtifactCost
}

export async function lineage(id: string){
  const r = await client.get(`/artifact/model/${id}/lineage`)
  return r.data
}

export async function licenseCheck(id: string, github_url: string){
  const r = await client.post(`/artifact/model/${id}/license-check`, { github_url })
  return r.data as boolean
}

export async function health(){
  const r = await client.get(`/health`)
  return r.data
}

export async function healthComponents(windowMinutes?: number, includeTimeline?: boolean){
  const r = await client.get('/health/components', { params: { windowMinutes, includeTimeline } })
  return r.data as T.HealthComponentCollection
}

export async function tracks(){
  const r = await client.get('/tracks')
  return r.data as { plannedTracks: string[] }
}

export async function resetAll(){
  await client.delete('/reset')
}
