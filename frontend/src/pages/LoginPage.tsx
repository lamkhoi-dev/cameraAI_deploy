import { useState, type FormEvent } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Lock, Eye, EyeOff, LogIn, Shield } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/", { replace: true });
    } catch {
      setError("Sai tên đăng nhập hoặc mật khẩu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col justify-between items-center bg-[#09090b] text-zinc-100 font-sans antialiased"
      style={{
        backgroundImage: "radial-gradient(circle, #27272a 1px, transparent 1px)",
        backgroundSize: "32px 32px",
      }}
    >
      {/* Main Content */}
      <main className="flex-grow flex items-center justify-center w-full px-6">
        <div className="w-full max-w-[420px] bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl relative overflow-hidden flex flex-col gap-6 p-6">
          {/* Header Badge */}
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-zinc-400" />
            <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-[0.15em]">
              CAMCORE AI
            </span>
          </div>

          {/* Logo Area */}
          <div className="flex flex-col items-center text-center gap-2 pt-4 pb-4">
            <div className="bg-zinc-800/50 p-4 rounded-full border border-zinc-700/50 mb-1">
              <Lock className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-2xl font-semibold text-white mt-2 tracking-tight">
              Đăng nhập hệ thống
            </h1>
            <p className="text-sm text-zinc-400">
              Quản lý camera &amp; AI giám sát
            </p>
          </div>

          {/* Divider */}
          <hr className="border-t border-zinc-800 w-full" />

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Username */}
            <div className="flex flex-col gap-1">
              <Label
                htmlFor="username"
                className="text-[12px] text-zinc-300 font-medium"
              >
                Tên đăng nhập
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="Tên đăng nhập"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="bg-[#09090b] border-zinc-700 text-white placeholder:text-zinc-500 focus-visible:ring-blue-600 focus-visible:border-transparent"
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1">
              <Label
                htmlFor="password"
                className="text-[12px] text-zinc-300 font-medium"
              >
                Mật khẩu
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Mật khẩu"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-[#09090b] border-zinc-700 text-white placeholder:text-zinc-500 focus-visible:ring-blue-600 focus-visible:border-transparent pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-zinc-500 hover:text-zinc-300"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
                {error}
              </p>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-10 bg-blue-600 hover:bg-blue-500 text-white font-medium mt-2 flex items-center justify-center gap-2"
            >
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
              <LogIn className="h-4 w-4" />
            </Button>
          </form>

          {/* Footer Text */}
          <div className="text-center mt-1">
            <p className="text-[12px] text-zinc-500">
              Phiên làm việc có hiệu lực 24 giờ
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-4 text-center">
        <p className="text-[11px] font-medium text-zinc-600 tracking-wider">
          © 2026 CamCore AI — v2.0
        </p>
      </footer>
    </div>
  );
}
