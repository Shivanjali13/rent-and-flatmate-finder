import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import ListingCard from '../components/ListingCard'

export default function BrowseListings() {
  const [listings, setListings] = useState([])
  const [location, setLocation] = useState('')
  const [minRent, setMinRent] = useState('')
  const [maxRent, setMaxRent] = useState('')
  const [sentIds, setSentIds] = useState(new Set())
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function loadListings() {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (location) params.location = location
      if (minRent) params.min_rent = minRent
      if (maxRent) params.max_rent = maxRent
      const res = await api.get('/browse', { params })
      setListings(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load listings. Have you set up your profile?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadListings()
    api.get('/interests/sent').then((res) => {
      setSentIds(new Set(res.data.map((i) => i.listing_id)))
    }).catch(() => {})
  }, [])

  async function expressInterest(listingId) {
    try {
      await api.post('/interests', { listing_id: listingId })
      setSentIds((prev) => new Set(prev).add(listingId))
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to send interest')
    }
  }

  return (
    <div className="page">
      <h2>Browse Listings</h2>
      <div className="filter-bar">
        <input placeholder="Filter by location" value={location} onChange={(e) => setLocation(e.target.value)} />
        <input placeholder="Min rent" type="number" value={minRent} onChange={(e) => setMinRent(e.target.value)} />
        <input placeholder="Max rent" type="number" value={maxRent} onChange={(e) => setMaxRent(e.target.value)} />
        <button onClick={loadListings}>Apply Filters</button>
      </div>

      {error && (
        <p className="error">
          {error} {error.includes('profile') && <Link to="/profile">Set up profile</Link>}
        </p>
      )}
      {loading && <p className="loading">Loading listings...</p>}

      <div className="listing-grid">
        {listings.map((listing) => (
          <ListingCard
            key={listing.id}
            listing={listing}
            onExpressInterest={expressInterest}
            interestSent={sentIds.has(listing.id)}
          />
        ))}
      </div>
      {!loading && listings.length === 0 && !error && <p>No listings match your filters yet.</p>}
    </div>
  )
}