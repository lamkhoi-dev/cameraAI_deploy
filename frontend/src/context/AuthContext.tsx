import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import api from "@/api/client";

interface User {
  username: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem("camcore_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem("camcore_token")
  );

  const isAuthenticated = !!token && !!user;

  useEffect(() => {
    if (user) localStorage.setItem("camcore_user", JSON.stringify(user));
    else localStorage.removeItem("camcore_user");
  }, [user]);

  useEffect(() => {
    if (token) localStorage.setItem("camcore_token", token);
    else localStorage.removeItem("camcore_token");
  }, [token]);

  const login = async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const res = await api.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    setToken(res.data.access_token);
    setUser({ username, role: res.data.role || "admin" });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("camcore_token");
    localStorage.removeItem("camcore_user");
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
