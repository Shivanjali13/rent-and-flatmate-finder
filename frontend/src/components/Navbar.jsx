import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">Rent & Flatmate Finder</Link>
      <div className="nav-links">
        {user?.role === 'tenant' && (
          <>
            <Link to="/browse">Browse</Link>
            <Link to="/profile">My Profile</Link>
            <Link to="/interests">My Interests</Link>
          </>
        )}
        {user?.role === 'owner' && (
          <>
            <Link to="/my-listings">My Listings</Link>
            <Link to="/interests">Interest Requests</Link>
          </>
        )}
        {user?.role === 'admin' && <Link to="/admin">Admin</Link>}
        {user ? (
          <>
            <span className="user-badge">{user.name} ({user.role})</span>
            <button onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  )
}