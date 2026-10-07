import React, { useState, useEffect } from "react";
import { api, UserContext } from "./api";
import { Login } from "./components/Login";
import { Dashboard } from "./components/Dashboard";

export const App: React.FC = () => {
  const [user, setUser] = useState<UserContext | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getMe().then((u) => {
      setUser(u);
      setLoading(false);
    });
  }, []);

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
  };

  if (loading) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "#090d16",
        color: "#94a3b8"
      }}>
        Loading Control Plane...
      </div>
    );
  }

  if (!user) {
    return <Login onSuccess={(u) => setUser(u)} />;
  }

  return <Dashboard user={user} onLogout={handleLogout} />;
};
