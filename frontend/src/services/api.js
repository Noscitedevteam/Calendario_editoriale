import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Se 401 e non è già un retry, prova a refreshare
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Prova a ottenere nuovo token con refresh
        const refreshResponse = await api.post('/auth/refresh');
        const newToken = refreshResponse.data.access_token;
        
        localStorage.setItem('token', newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh fallito, vai al login
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;

export const auth = {
  login: (email, password) => api.post('/auth/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const brands = {
  list: () => api.get('/brands/'),
  get: (id) => api.get(`/brands/${id}`),
  create: (data) => api.post('/brands/', data),
  update: (id, data) => api.put(`/brands/${id}`, data),
  delete: (id) => api.delete(`/brands/${id}`),
};

export const projects = {
  list: (brandId) => api.get('/projects/', { params: { brand_id: brandId } }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects/', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
};

export const posts = {
  list: (projectId) => api.get(`/posts/project/${projectId}`),
  listByProject: (projectId) => api.get(`/posts/project/${projectId}`),
  get: (id) => api.get(`/posts/${id}`),
  update: (id, data) => api.patch(`/posts/${id}`, data),
  delete: (id) => api.delete(`/posts/${id}`),
  createManual: (data) => api.post('/posts/manual', data),
  generateAI: (data) => api.post('/posts/generate-ai', data),
  batchDelete: (postIds) => api.post('/posts/batch-delete', { post_ids: postIds }),
  batchReplace: (postIds, brief) => api.post('/posts/batch-replace', { post_ids: postIds, brief }),
  regenerate: (id, prompt) => api.post(`/posts/${id}/regenerate`, { prompt }),
  generateImage: (id) => api.post(`/posts/${id}/generate-image`),
};

export const generation = {
  generateCalendar: (projectId) => api.post(`/generate/calendar/${projectId}`),
  getStatus: (projectId) => api.get(`/generate/status/${projectId}`),
  // Personas
  generatePersonas: (projectId) => api.post(`/generate/personas/${projectId}`),
  regeneratePersonas: (projectId, feedback) => api.post(`/generate/personas/${projectId}/regenerate`, { feedback }),
  confirmPersonas: (projectId, personas) => api.put(`/generate/personas/${projectId}/confirm`, { personas }),
  getPersonas: (projectId) => api.get(`/generate/personas/${projectId}`),
  // Singola persona
  addPersona: (projectId, description) => api.post(`/generate/personas/${projectId}/add`, { persona_description: description }),
  deletePersona: (projectId, index) => api.delete(`/generate/personas/${projectId}/${index}`),
  regeneratePersona: (projectId, index, description) => api.post(`/generate/personas/${projectId}/${index}/regenerate`, { persona_description: description }),
};
