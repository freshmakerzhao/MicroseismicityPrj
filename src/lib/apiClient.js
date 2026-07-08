const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api"
const TOKEN_KEY = "rockburst_auth_token"
const USER_KEY = "rockburst_auth_user"

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  const contentType = response.headers.get("content-type") || ""
  const payload = contentType.includes("application/json") ? await response.json() : await response.text()
  if (!response.ok) {
    const message = payload && payload.detail ? payload.detail : `HTTP ${response.status}`
    throw new Error(message)
  }
  return payload
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ""
}

export function getCurrentUser() {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (error) {
    return null
  }
}

export function isLoggedIn() {
  return !!getToken() && !!getCurrentUser()
}

export function isAdmin() {
  const user = getCurrentUser()
  return user && user.role === "admin"
}

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export async function login(payload) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  })
  saveSession(data.token, data.user)
  return data
}

export function register(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export async function logout() {
  try {
    await request("/auth/logout", { method: "POST" })
  } finally {
    clearSession()
  }
}

export function fetchUsers() {
  return request("/users").then((data) => data.users || [])
}

export function updateUser(id, payload) {
  return request(`/users/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export function deleteUser(id) {
  return request(`/users/${id}`, { method: "DELETE" })
}

export function generateSurferMap(file) {
  const form = new FormData()
  form.append("file", file)
  return request("/generate-surfer", {
    method: "POST",
    body: form,
  })
}
