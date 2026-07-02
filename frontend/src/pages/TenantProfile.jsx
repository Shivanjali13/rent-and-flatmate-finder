import { useEffect, useState } from 'react'
import api from '../api'

export default function TenantProfile() {
  const [form, setForm] = useState({
    preferred_location: '', budget_min: '', budget_max: '', move_in_date: '', notes: '',
  })
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/tenants/profile')
      .then((res) => {
        const p = res.data
        setForm({
          preferred_location: p.preferred_location,
          budget_min: p.budget_min,
          budget_max: p.budget_max,
          move_in_date: p.move_in_date,
          notes: p.notes || '',
        })
      })
      .catch(() => {}) // 404 = no profile yet, that's fine
      .finally(() => setLoading(false))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('Saving...')
    try {
      await api.put('/tenants/profile', {
        ...form,
        budget_min: Number(form.budget_min),
        budget_max: Number(form.budget_max),
      })
      setStatus('Saved!')
    } catch (err) {
      setStatus(err.response?.data?.detail || 'Failed to save')
    }
  }

  if (loading) return <p className="loading">Loading...</p>

  return (
    <div className="page">
      <h2>My Preferences</h2>
      <form onSubmit={handleSubmit} className="form-card">
        <label>Preferred Location</label>
        <input
          value={form.preferred_location}
          onChange={(e) => setForm({ ...form, preferred_location: e.target.value })}
          required
        />
        <label>Budget Min (₹)</label>
        <input
          type="number" value={form.budget_min}
          onChange={(e) => setForm({ ...form, budget_min: e.target.value })}
          required
        />
        <label>Budget Max (₹)</label>
        <input
          type="number" value={form.budget_max}
          onChange={(e) => setForm({ ...form, budget_max: e.target.value })}
          required
        />
        <label>Move-in Date</label>
        <input
          type="date" value={form.move_in_date}
          onChange={(e) => setForm({ ...form, move_in_date: e.target.value })}
          required
        />
        <label>Notes (optional - fed into AI matching)</label>
        <textarea
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          placeholder="e.g. non-smoker, prefer quiet flatmates, need parking"
        />
        <button type="submit">Save Preferences</button>
        {status && <p className="status">{status}</p>}
      </form>
    </div>
  )
}