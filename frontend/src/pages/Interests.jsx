import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function Interests() {
  const { user } = useAuth()
  const [interests, setInterests] = useState([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    const endpoint = user.role === 'owner' ? '/interests/received' : '/interests/sent'
    const res = await api.get(endpoint)
    setInterests(res.data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function respond(id, status) {
    await api.patch(`/interests/${id}`, { status })
    load()
  }

  if (loading) return <p className="loading">Loading...</p>

  return (
    <div className="page">
      <h2>{user.role === 'owner' ? 'Interest Requests Received' : 'My Interest Requests'}</h2>
      <div className="interest-list">
        {interests.map((i) => (
          <div key={i.id} className="interest-card">
            <div className="interest-header">
              <h4>{i.listing_location} · ₹{i.listing_rent.toLocaleString('en-IN')}/mo</h4>
              <span className={`status-badge status-${i.status}`}>{i.status}</span>
            </div>
            <p>
              {user.role === 'owner' ? 'From' : 'To'}: <strong>{i.other_party_name}</strong> ({i.other_party_email})
            </p>
            {i.compatibility_score != null && (
              <p>Compatibility score: <strong>{i.compatibility_score}/100</strong> — {i.compatibility_explanation}</p>
            )}
            <div className="interest-actions">
              {user.role === 'owner' && i.status === 'pending' && (
                <>
                  <button onClick={() => respond(i.id, 'accepted')}>Accept</button>
                  <button className="secondary" onClick={() => respond(i.id, 'declined')}>Decline</button>
                </>
              )}
              {i.status === 'accepted' && (
                <Link to={`/chat/${i.id}`}><button>Open Chat</button></Link>
              )}
            </div>
          </div>
        ))}
      </div>
      {interests.length === 0 && <p>No interest requests yet.</p>}
    </div>
  )
}