// Lớp gọi API phía frontend – ánh xạ 1–1 với 20 API trong hợp đồng (docs/openapi.json; phiên bản đọc từ /api/health).
// backend/tests/test_frontend_contract.py đối chiếu tệp này và các màn hình với hợp đồng: đường dẫn, tên tham số, trường
// thân yêu cầu, giới hạn page_size… – sửa API ở backend mà quên sửa ở đây thì pytest/CI báo lỗi.
import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 120000 })

// Lỗi thống nhất: { error: { code, message, details } }
export const errorMessage = (e) => {
  if (e?.response?.data?.error?.message) return e.response.data.error.message
  if (e?.code === 'ECONNABORTED') return 'Máy chủ phản hồi quá lâu, vui lòng thử lại'
  // Vite (npm run dev, cả trong Docker) trả 500 với thân rỗng khi không nối được backend – trước đây chỉ hiện
  // "Request failed with status code 500"; lỗi 500 thật của FastAPI luôn có nội dung nên không bị nhầm
  const proxyDown = e?.response?.status === 500 && !e?.response?.data
  if (e?.message === 'Network Error' || proxyDown || e?.response?.status === 502 || e?.response?.status === 504)
    // chạy thường: backend ở http://localhost:8000; chạy Docker: frontend chuyển /api tới http://backend:8000
    return 'Không kết nối được backend (cổng 8000) – hãy kiểm tra máy chủ FastAPI hoặc container backend đang chạy'
  return e?.message || 'Lỗi không xác định'
}
export const errorCode = (e) => e?.response?.data?.error?.code

const clean = (p) => Object.fromEntries(Object.entries(p || {}).filter(([, v]) => v !== '' && v != null))

export const api = {
  health: () => http.get('/health').then((r) => r.data),
  upload: (file, onProgress) => {
    const fd = new FormData(); fd.append('file', file)
    return http.post('/upload', fd, { timeout: 600000, onUploadProgress: (e) => onProgress?.(Math.round((e.loaded / (e.total || 1)) * 100)) }).then((r) => r.data)
  },
  job: (jobId) => http.get(`/jobs/${jobId}`).then((r) => r.data),
  useSample: (kind = 'sample') => http.post('/data/sample', null, { params: { kind }, timeout: 300000 }).then((r) => r.data),
  quality: () => http.get('/data/quality').then((r) => r.data),
  reset: () => http.post('/session/reset').then((r) => r.data),
  kpi: (filters = {}) => http.get('/kpi', { params: clean(filters) }).then((r) => r.data),
  eda: (chart, filters = {}) => http.get(`/eda/${chart}`, { params: clean(filters) }).then((r) => r.data),
  modelMetrics: () => http.get('/model/metrics').then((r) => r.data),
  modelKeywords: (n = 15) => http.get('/model/keywords', { params: { n } }).then((r) => r.data),
  mismatch: (params = {}) => http.get('/reviews/mismatch', { params: clean(params) }).then((r) => r.data),
  predict: (body) => http.post('/predict', body).then((r) => r.data),
  topics: (productId) => http.get('/topics', { params: clean({ product_id: productId }) }).then((r) => r.data),
  satisfaction: (params = {}) => http.get('/satisfaction', { params: clean(params) }).then((r) => r.data),
  forecast: (params = {}) => http.get('/forecast', { params: clean(params) }).then((r) => r.data),
  products: (params = {}) => http.get('/products', { params: clean(params) }).then((r) => r.data),
  aiInsights: (body) => http.post('/ai/insights', body, { timeout: 180000 }).then((r) => r.data),
  chat: (body) => http.post('/chat', body, { timeout: 180000 }).then((r) => r.data),
  reportPdfUrl: () => '/api/report/pdf',
  exportUrl: (table) => `/api/export/${table}`,
}
