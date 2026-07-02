import { useEffect, useState } from 'react'
import api from '../api'

const emptyForm = {
  location: '', rent: '', available_from: '', room_type: 'single',
  furnishing_status: 'furnished', photos: '', description: '',
}

export default function OwnerListings() {
  const [listings, setListings] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [showForm, setShowForm] = useState(false)
  const [status, setStatus] = useState('')

  async function loadListings() {
    const res = await api.get('/listings/mine')
    setListings(res.data)
  }

  useEffect(() => { loadListings() }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('Saving...')
    try {
      await api.post('/listings', {
        ...form,
        rent: Number(form.rent),
        photos: form.photos ? form.photos.split(',').map((p) => p.trim()) : [],
      })
      setForm(emptyForm)
      setShowForm(false)
      setStatus('')
      loadListings()
    } catch (err) {
      setStatus(err.response?.data?.detail || 'Failed to create listing')
    }
  }

  async function markFilled(id) {
    if (!confirm('Mark this listing as filled? It will be hidden from search results.')) return
    await api.post(`/listings/${id}/mark-filled`)
    loadListings()
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>My Listings</h2>
        <button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Listing'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="form-card">
          <label>Location</label>
          <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} required />
          <label>Rent (₹/month)</label>
          <input type="number" value={form.rent} onChange={(e) => setForm({ ...form, rent: e.target.value })} required />
          <label>Available From</label>
          <input type="date" value={form.available_from} onChange={(e) => setForm({ ...form, available_from: e.target.value })} required />
          <label>Room Type</label>
          <select value={form.room_type} onChange={(e) => setForm({ ...form, room_type: e.target.value })}>
            <option value="single">Single Room</option>
            <option value="shared">Shared Room</option>
            <option value="1BHK">1 BHK</option>
            <option value="2BHK">2 BHK</option>
          </select>
          <label>Furnishing</label>
          <select value={form.furnishing_status} onChange={(e) => setForm({ ...form, furnishing_status: e.target.value })}>
            <option value="furnished">Furnished</option>
            <option value="semi-furnished">Semi-furnished</option>
            <option value="unfurnished">Unfurnished</option>
          </select>
          <label>Photo URLs (comma separated, optional)</label>
          <input value={form.photos} onChange={(e) => setForm({ ...form, photos: e.target.value })} placeholder="https://..." />
          <label>Description</label>
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <button type="submit">Create Listing</button>
          {status && <p className="status">{status}</p>}
        </form>
      )}

      <div className="listing-grid">
        {listings.map((l) => (
          <div key={l.id} className="listing-card">
            {l.photos?.[0] && <img src={l.photos[0]} alt={l.location} className="listing-photo" />}
            <div className="listing-body">
              <div className="listing-header">
                <h3>{l.location}</h3>
                <span className={`status-badge status-${l.status}`}>{l.status}</span>
              </div>
              <p className="rent">₹{l.rent.toLocaleString('en-IN')}/month</p>
              <p>{l.room_type} · {l.furnishing_status}</p>
              <p>Available from {l.available_from}</p>
              {l.status === 'active' && (
                <button onClick={() => markFilled(l.id)}>Mark as Filled</button>
              )}
            </div>
          </div>
        ))}
      </div>
      {listings.length === 0 && <p>You haven't posted any listings yet.</p>}
    </div>
  )
}