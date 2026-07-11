import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(email, password)
      if (user.role === 'tenant') navigate('/browse')
      else if (user.role === 'owner') navigate('/my-listings')
      else navigate('/admin')
    } catch (err) {
      console.error('Login error:', err)
      setError(err.response?.data?.detail || `Login failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Log In</h2>
        {error && <p className="error">{error}</p>}
        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit" disabled={loading}>{loading ? 'Logging in...' : 'Log In'}</button>
        <p>No account? <Link to="/register">Register</Link></p>
      </form>
    </div>
  )
}