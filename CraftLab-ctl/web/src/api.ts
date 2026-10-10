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

export interface UpdateCheckResult {
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  published_at?: string;
  release_notes?: string;
  message: string;
}

export interface ReleasesInfo {
  installed_releases: string[];
  active_release: string | null;
  maintenance: {
    enabled: boolean;
    message: string;
    enabled_at: string | null;
  };
}

export interface OperationResponse {
  success: boolean;
  message?: string;
  error?: string;
  data?: any;
  steps?: Array<{
    step: string;
    status: string;
  }>;
}

export interface SecurityPosture {
  threat_index: number;
  classification: "NORMAL" | "ELEVATED" | "HIGH" | "CRITICAL" | "LOCKDOWN";
  failed_auths_15m: number;
  active_alerts_count: number;
  quarantined_ips_count: number;
  lockdown_enabled: boolean;
  evaluated_at: string;
}

export interface SecurityAnomaly {
  alert_id: string;
  rule: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  source_ip?: string;
  target_actor?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface SecurityQuarantineEntry {
  ip: string;
  reason: string;
  created_at: string;
  expires_at: string;
  quarantined_by: string;
}

export interface SecurityEventRecord {
  event_id: string;
  schema_version: number;
  occurred_at: string;
  received_at: string;
  component: string;
  event_type: string;
  severity: string;
  outcome: string;
  actor_type: string;
  actor_id?: string;
  source_ip?: string;
  source_transport: string;
  route?: string;
  method?: string;
  status_code?: number;
  reason_code?: string;
  operation_id?: string;
  request_id?: string;
  duration_ms?: number;
  attributes_json: string;
}

export interface SecurityEventsResponse {
  events: SecurityEventRecord[];
  total: number;
  limit: number;
  offset: number;
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

  async getReleases(): Promise<ReleasesInfo> {
    const res = await fetch("/api/v1/update/releases", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch releases");
    return await res.json();
  },

  async checkUpdates(repo?: string): Promise<UpdateCheckResult> {
    const url = repo ? `/api/v1/update/check?repo=${encodeURIComponent(repo)}` : "/api/v1/update/check";
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) throw new Error("Failed to check for updates");
    return await res.json();
  },

  async prepareUpdate(version: string, repo?: string, localFile?: string): Promise<OperationResponse> {
    const res = await fetch("/api/v1/update/prepare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ version, github_repo: repo, local_file: localFile }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || "Prepare update failed");
    }
    return await res.json();
  },

  async applyUpdate(version: string, timeout = 15): Promise<OperationResponse> {
    const res = await fetch("/api/v1/update/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ version, timeout }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || "Apply update failed");
    }
    return await res.json();
  },

  async rollbackUpdate(targetVersion?: string, timeout = 15): Promise<OperationResponse> {
    const res = await fetch("/api/v1/update/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ target_version: targetVersion, timeout }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || "Rollback failed");
    }
    return await res.json();
  },

  async getMaintenance(): Promise<any> {
    const res = await fetch("/api/v1/update/maintenance", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch maintenance status");
    return await res.json();
  },

  async setMaintenance(enable: boolean, message?: string): Promise<any> {
    const res = await fetch("/api/v1/update/maintenance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ enable, message: message || "" }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || "Set maintenance failed");
    }
    return await res.json();
  },

  createLogWebSocket(): WebSocket {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return new WebSocket(`${protocol}//${window.location.host}/api/v1/ws/logs`);
  },

  async getSecurityPosture(): Promise<SecurityPosture> {
    const res = await fetch("/api/v1/security/posture", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch security posture");
    return await res.json();
  },

  async getSecurityAnomalies(): Promise<SecurityAnomaly[]> {
    const res = await fetch("/api/v1/security/anomalies", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch security anomalies");
    return await res.json();
  },

  async dismissSecurityAnomaly(alertId: string): Promise<void> {
    const res = await fetch("/api/v1/security/anomalies/dismiss", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ alert_id: alertId }),
    });
    if (!res.ok) throw new Error("Failed to dismiss security anomaly");
  },

  async getSecurityEvents(params?: {
    component?: string;
    event_type?: string;
    severity?: string;
    outcome?: string;
    limit?: number;
    offset?: number;
  }): Promise<SecurityEventsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.component) searchParams.set("component", params.component);
    if (params?.event_type) searchParams.set("event_type", params.event_type);
    if (params?.severity) searchParams.set("severity", params.severity);
    if (params?.outcome) searchParams.set("outcome", params.outcome);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());

    const res = await fetch(`/api/v1/security/events?${searchParams.toString()}`, {
      credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch security events");
    return await res.json();
  },

  async getSecurityQuarantines(): Promise<SecurityQuarantineEntry[]> {
    const res = await fetch("/api/v1/security/quarantines", { credentials: "include" });
    if (!res.ok) throw new Error("Failed to fetch quarantined IPs");
    return await res.json();
  },

  async quarantineIp(ip: string, durationMinutes = 60, reason = "Manual quarantine"): Promise<OperationResponse> {
    const res = await fetch("/api/v1/security/quarantine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ ip, duration_minutes: durationMinutes, reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to quarantine IP");
    }
    return await res.json();
  },

  async unquarantineIp(ip: string): Promise<OperationResponse> {
    const res = await fetch("/api/v1/security/unquarantine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ ip }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to unquarantine IP");
    }
    return await res.json();
  },

  async revokeSessions(username?: string, allExceptCaller = true): Promise<OperationResponse> {
    const res = await fetch("/api/v1/security/revoke-sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, all_except_caller: allExceptCaller }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to revoke sessions");
    }
    return await res.json();
  },

  async toggleLockdown(enabled: boolean, reason = ""): Promise<OperationResponse> {
    const res = await fetch("/api/v1/security/toggle-lockdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ enabled, reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to toggle lockdown");
    }
    return await res.json();
  },

  async purgeSecurityLogs(retentionDays = 30): Promise<OperationResponse> {
    const res = await fetch("/api/v1/security/purge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ retention_days: retentionDays }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to purge security logs");
    }
    return await res.json();
  },
};
