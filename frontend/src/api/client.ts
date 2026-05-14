import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

let authToken: string | null = localStorage.getItem("auth_token");

/** Auto-login with default credentials */
async function autoLogin(): Promise<string | null> {
  try {
    const res = await axios.post(`${API_BASE}/auth/login`, {
      username: "admin",
      password: "admin123",
    });
    const token = res.data.access_token;
    if (token) {
      localStorage.setItem("auth_token", token);
      authToken = token;
      return token;
    }
  } catch {
    console.warn("Auto-login failed");
  }
  return null;
}

// Request interceptor: attach token
api.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

// Response interceptor: retry on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const token = await autoLogin();
      if (token) {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  }
);

// Initial login on module load
if (!authToken) {
  autoLogin();
}

export default api;
