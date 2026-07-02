import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'

import Login from './pages/Login'
import Register from './pages/Register'
import TenantProfile from './pages/TenantProfile'
import BrowseListings from './pages/BrowseListings'
import OwnerListings from './pages/OwnerListings'
import Interests from './pages/Interests'
import Chat from './pages/Chat'
import AdminDashboard from './pages/AdminDashboard'

function Home() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'tenant') return <Navigate to="/browse" replace />
  if (user.role === 'owner') return <Navigate to="/my-listings" replace />
  return <Navigate to="/admin" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <main>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<Home />} />

            <Route path="/profile" element={
              <ProtectedRoute allowedRoles={['tenant']}><TenantProfile /></ProtectedRoute>
            } />
            <Route path="/browse" element={
              <ProtectedRoute allowedRoles={['tenant']}><BrowseListings /></ProtectedRoute>
            } />
            <Route path="/my-listings" element={
              <ProtectedRoute allowedRoles={['owner']}><OwnerListings /></ProtectedRoute>
            } />
            <Route path="/interests" element={
              <ProtectedRoute allowedRoles={['tenant', 'owner']}><Interests /></ProtectedRoute>
            } />
            <Route path="/chat/:interestId" element={
              <ProtectedRoute allowedRoles={['tenant', 'owner']}><Chat /></ProtectedRoute>
            } />
            <Route path="/admin" element={
              <ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>
            } />
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  )
}