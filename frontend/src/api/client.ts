import axios from 'axios'

const baseURL = (import.meta as any).env.VITE_API_URL || ''

export const client = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers = { ...cfg.headers, 'X-Authorization': token }
  return cfg
})

client.interceptors.response.use(
  (r) => r,
  (err) => {
    console.error('API error', err?.response || err)
    return Promise.reject(err)
  }
)

export default client
