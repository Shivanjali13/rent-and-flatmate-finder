import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('tenant')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await register(name, email, password, role)
      if (user.role === 'tenant') navigate('/profile')
      else if (user.role === 'owner') navigate('/my-listings')
      else navigate('/admin')
    } catch (err) {
      console.error('Registration error:', err)
      setError(err.response?.data?.detail || `Registration failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Create Account</h2>
        {error && <p className="error">{error}</p>}
        <label>Name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} required />
        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        <label>I am a...</label>
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="tenant">Tenant (looking for a room)</option>
          <option value="owner">Owner (listing a room)</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Register'}</button>
        <p>Already have an account? <Link to="/login">Log in</Link></p>
      </form>
    </div>
  )
}