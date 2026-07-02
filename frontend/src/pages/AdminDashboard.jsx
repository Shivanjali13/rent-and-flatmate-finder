import { useEffect, useState } from 'react'
import api from '../api'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [listings, setListings] = useState([])
  const [tab, setTab] = useState('stats')

  useEffect(() => {
    api.get('/admin/stats').then((res) => setStats(res.data))
    api.get('/admin/users').then((res) => setUsers(res.data))
    api.get('/admin/listings').then((res) => setListings(res.data))
  }, [])

  async function toggleUser(u) {
    const action = u.is_active ? 'deactivate' : 'activate'
    await api.post(`/admin/users/${u.id}/${action}`)
    setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: !x.is_active } : x)))
  }

  async function deleteListing(id) {
    if (!confirm('Delete this listing permanently?')) return
    await api.delete(`/admin/listings/${id}`)
    setListings((prev) => prev.filter((l) => l.id !== id))
  }

  return (
    <div className="page">
      <h2>Admin Dashboard</h2>
      <div className="tab-bar">
        <button className={tab === 'stats' ? 'active' : ''} onClick={() => setTab('stats')}>Stats</button>
        <button className={tab === 'users' ? 'active' : ''} onClick={() => setTab('users')}>Users</button>
        <button className={tab === 'listings' ? 'active' : ''} onClick={() => setTab('listings')}>Listings</button>
      </div>

      {tab === 'stats' && stats && (
        <div className="stats-grid">
          <div className="stat-card"><h3>{stats.total_users}</h3><p>Total Users</p></div>
          <div className="stat-card"><h3>{stats.total_listings}</h3><p>Total Listings</p></div>
          <div className="stat-card"><h3>{stats.total_interests}</h3><p>Total Interests</p></div>
          <div className="stat-card"><h3>{stats.total_messages}</h3><p>Chat Messages</p></div>
          <pre className="stat-detail">{JSON.stringify(stats, null, 2)}</pre>
        </div>
      )}

      {tab === 'users' && (
        <table className="admin-table">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td><td>{u.email}</td><td>{u.role}</td>
                <td>{u.is_active ? 'Active' : 'Deactivated'}</td>
                <td><button onClick={() => toggleUser(u)}>{u.is_active ? 'Deactivate' : 'Activate'}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === 'listings' && (
        <table className="admin-table">
          <thead><tr><th>Location</th><th>Rent</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {listings.map((l) => (
              <tr key={l.id}>
                <td>{l.location}</td><td>₹{l.rent}</td><td>{l.status}</td>
                <td><button onClick={() => deleteListing(l.id)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}