import { createContext, useContext, useState } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  })

  async function login(email, password) {
    // Login uses OAuth2PasswordRequestForm on the backend, which expects
    // application/x-www-form-urlencoded with a 'username' field.
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    setUser(res.data.user)
    return res.data.user
  }

  async function register(name, email, password, role) {
    await api.post('/auth/register', { name, email, password, role })
    return login(email, password)
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}