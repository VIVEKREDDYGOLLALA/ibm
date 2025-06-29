import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8004';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minute timeout for heavy operations
});

// Request interceptor for logging and auth
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    console.error(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      // Note: Redirect logic can be handled by components
    }
    return Promise.reject(error);
  }
);

const apiService = {
  // Health check
  healthCheck: () => api.get('/api/health'),
  
  // Simple health for quick checks
  simpleHealth: () => api.get('/'),

  // Jira endpoints
  getJiraIssues: (projectKey, status = null, maxResults = 50) => {
    const params = { project_key: projectKey, max_results: maxResults };
    if (status) params.status = status;
    return api.get('/api/jira/issues', { params });
  },

  getJiraProjects: () => api.get('/api/jira/projects'),

  getJiraIssue: (issueKey) => api.get(`/api/jira/issue/${issueKey}`),

  // Implementation plan generation
  generateImplementationPlan: (data) => {
    console.log('🎯 Generating implementation plan with Granite AI...');
    return api.post('/api/generate-implementation-plan', data);
  },

  // PR validation
  validatePR: (data) => {
    console.log('🔍 Validating PR with Granite AI...');
    return api.post('/api/validate-pr', data);
  },

  // Download PDF
  downloadPDF: (filename) => {
    return api.get(`/api/download-pdf/${filename}`, {
      responseType: 'blob',
    });
  },

  // Test API connectivity
  testConnection: async () => {
    try {
      const response = await api.get('/api/health');
      return {
        success: true,
        status: response.data.status,
        services: response.data.services
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        details: error.response?.data
      };
    }
  },

  // Test IBM Granite connection specifically
  testGraniteConnection: () => api.get('/api/test-granite'),

  // Test simple text generation
  testSimpleGeneration: (data) => api.post('/api/test-simple-generation', data),

  // Test PR validation functionality
  testPRValidation: (data) => api.post('/api/test-pr-validation', data)
};

export default apiService; 