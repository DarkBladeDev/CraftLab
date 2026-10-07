import React, { useState } from "react";
import { api, UserContext } from "../api";

interface LoginProps {
  onSuccess: (user: UserContext) => void;
}

export const Login: React.FC<LoginProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await api.login(username, password);
      onSuccess(user);
    } catch (err: any) {
      setError(err.message || "Failed to sign in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      backgroundColor: "#090d16",
      padding: "1rem"
    }}>
      <div style={{
        width: "100%",
        maxWidth: "400px",
        backgroundColor: "#131b2e",
        border: "1px solid #1e293b",
        borderRadius: "12px",
        padding: "2rem",
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)"
      }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "48px",
            height: "48px",
            backgroundColor: "#2563eb",
            borderRadius: "10px",
            color: "white",
            fontWeight: "bold",
            fontSize: "20px",
            marginBottom: "0.75rem"
          }}>
            CL
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: "700", margin: "0 0 0.5rem 0", color: "#f8fafc" }}>
            CraftLab Control Plane
          </h1>
          <p style={{ margin: 0, color: "#94a3b8", fontSize: "0.875rem" }}>
            Sign in to manage server runtime & diagnostics
          </p>
        </div>

        {error && (
          <div style={{
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            border: "1px solid #ef4444",
            color: "#fca5a5",
            padding: "0.75rem",
            borderRadius: "6px",
            fontSize: "0.875rem",
            marginBottom: "1.25rem"
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", color: "#cbd5e1", fontSize: "0.875rem", marginBottom: "0.375rem" }}>
              Username
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin or dev"
              style={{
                width: "100%",
                padding: "0.625rem 0.75rem",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "0.875rem",
                outline: "none"
              }}
            />
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", color: "#cbd5e1", fontSize: "0.875rem", marginBottom: "0.375rem" }}>
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{
                width: "100%",
                padding: "0.625rem 0.75rem",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "0.875rem",
                outline: "none"
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.75rem",
              backgroundColor: loading ? "#1e40af" : "#2563eb",
              border: "none",
              borderRadius: "6px",
              color: "white",
              fontWeight: "600",
              fontSize: "0.875rem",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background-color 0.15s"
            }}
          >
            {loading ? "Authenticating..." : "Sign In to Control Plane"}
          </button>
        </form>
      </div>
    </div>
  );
};
