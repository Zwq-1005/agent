import axios from 'axios'
import { useMessage } from 'naive-ui'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string'
      ? detail
      : error.message || '请求失败'

    console.error('[API Error]', message, error.response?.status)
    return Promise.reject(error)
  }
)

export default apiClient
