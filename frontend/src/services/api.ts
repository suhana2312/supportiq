const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, any>;
}

export async function apiRequest<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const token = localStorage.getItem("supportiq_access_token");
  
  let url = `${BASE_URL}${endpoint}`;
  if (options.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        searchParams.append(k, String(v));
      }
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response = await fetch(url, {
    ...options,
    headers,
  });

  // Attempt automatic token refresh on 401
  if (response.status === 401 && !endpoint.includes("/auth/")) {
    const refreshToken = localStorage.getItem("supportiq_refresh_token");
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshRes.ok) {
          const refreshData = await refreshRes.json();
          if (refreshData.success && refreshData.data) {
            localStorage.setItem("supportiq_access_token", refreshData.data.access_token);
            localStorage.setItem("supportiq_refresh_token", refreshData.data.refresh_token);
            headers["Authorization"] = `Bearer ${refreshData.data.access_token}`;
            // Retry original request
            response = await fetch(url, { ...options, headers });
          }
        } else {
          // Token refresh expired, clear credentials
          localStorage.removeItem("supportiq_access_token");
          localStorage.removeItem("supportiq_refresh_token");
          localStorage.removeItem("supportiq_user");
          window.location.href = "/login";
        }
      } catch (e) {
        console.error("Token refresh failed", e);
      }
    }
  }

  const data = await response.json();
  if (!response.ok || !data.success) {
    const errMsg = data?.error?.message || "An error occurred while communicating with SupportIQ API";
    throw new Error(errMsg);
  }

  return data.data;
}
