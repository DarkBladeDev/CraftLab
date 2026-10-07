export interface UserContext {
  user_id: string;
  username: string;
  roles: string[];
  is_break_glass?: boolean;
}

export interface ServiceStatus {
  service: string;
  supervisor: string;
  is_running: boolean;
  status: string;
  pid: number | null;
  uptime_seconds?: number;
  memory_mb?: number;
}

export interface SystemMetrics {
  timestamp: number;
  host: {
    cpu_percent: number;
    memory: {
      total_mb: number;
      used_mb: number;
      free_bytes: number;
      percent: number;
    };
    disk: {
      total_gb: number;
      free_gb: number;
      percent: number;
    };
  };
  process: {
    status: string;
    pid: number | null;
    cpu_percent: number;
    memory_mb: number;
    threads: number;
    uptime_seconds: number;
  };
}

export interface DoctorResult {
  overall: "PASS" | "WARN" | "FAIL";
  checks: Array<{
    check_id: string;
    status: string;
    message: string;
  }>;
}

export const api = {
  async getMe(): Promise<UserContext | null> {
    try {
      const res = await fetch("/api/v1/auth/me", { credentials: "include" });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  async login(username: string, password: string): Promise<UserContext> {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    return await res.json();
  },

  async logout(): Promise<void> {
    await fetch("/api/v1/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  },

  async getStatus(): Promise<ServiceStatus> {
    const res = await fetch("/api/v1/status", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch status");
    return await res.json();
  },

  async getMetrics(): Promise<SystemMetrics> {
    const res = await fetch("/api/v1/metrics", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return await res.json();
  },

  async getDoctor(): Promise<DoctorResult> {
    const res = await fetch("/api/v1/doctor", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to run doctor");
    return await res.json();
  },

  async executeLifecycle(action: string): Promise<any> {
    const res = await fetch(`/api/v1/lifecycle/${action}`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Action ${action} failed`);
    }
    return await res.json();
  },

  createLogWebSocket(): WebSocket {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return new WebSocket(`${protocol}//${window.location.host}/api/v1/ws/logs`);
  },
};
