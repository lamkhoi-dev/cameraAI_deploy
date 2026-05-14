import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// JWT interceptor — attach token from AuthContext
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("camcore_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 → clear auth state and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("camcore_token");
      localStorage.removeItem("camcore_user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
