import React, { createContext, useContext, useState, useEffect } from "react";
import { User, TokenResponse } from "../types";
import { apiRequest } from "../services/api";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, orgName: string) => Promise<void>;
  logout: () => void;
  quickLogin: (role: "admin" | "agent" | "customer") => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const savedUser = localStorage.getItem("supportiq_user");
    const token = localStorage.getItem("supportiq_access_token");
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.clear();
      }
    }
    setIsLoading(false);
  }, []);

  const saveAuthSession = (tokens: TokenResponse) => {
    localStorage.setItem("supportiq_access_token", tokens.access_token);
    localStorage.setItem("supportiq_refresh_token", tokens.refresh_token);
    localStorage.setItem("supportiq_user", JSON.stringify(tokens.user));
    setUser(tokens.user);
  };

  const login = async (email: string, password: string) => {
    const data = await apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    saveAuthSession(data);
  };

  const register = async (name: string, email: string, password: string, orgName: string) => {
    const data = await apiRequest<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, organization_name: orgName }),
    });
    saveAuthSession(data);
  };

  const logout = () => {
    const refreshToken = localStorage.getItem("supportiq_refresh_token");
    if (refreshToken) {
      apiRequest("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => {});
    }
    localStorage.removeItem("supportiq_access_token");
    localStorage.removeItem("supportiq_refresh_token");
    localStorage.removeItem("supportiq_user");
    setUser(null);
    window.location.href = "/login";
  };

  const quickLogin = async (role: "admin" | "agent" | "customer") => {
    let email = "customer1@example.com";
    let password = "Customer123!";
    if (role === "admin") {
      email = "admin@supportiq.com";
      password = "Admin123!";
    } else if (role === "agent") {
      email = "agent.sarah@supportiq.com";
      password = "Agent123!";
    }
    await login(email, password);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout, quickLogin }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
