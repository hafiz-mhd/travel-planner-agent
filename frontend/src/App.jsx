import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { UserProvider, useUser } from './hooks/useUser'
import PlannerPage from './pages/PlannerPage'
import TripsPage from './pages/TripsPage'
import TripDetailPage from './pages/TripDetailPage'
import LoginPage from './pages/LoginPage'

function Shell() {
  const { user, logout } = useUser()
  const initials = user ? user.name.split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase() : ''

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="navbar-brand">
          <span className="navbar-logo">✈️</span>
          Travel Planner
        </div>

        <div className="navbar-links">
          {user ? (
            <>
              <NavLink to="/" end>✦ Plan Trip</NavLink>
              <NavLink to="/trips">🗂 My Trips</NavLink>
              <div className="navbar-user">
                <div className="navbar-avatar">{initials}</div>
                <span>{user.name}</span>
                <span className="navbar-signout" onClick={logout} title="Sign out">✕</span>
              </div>
            </>
          ) : (
            <NavLink to="/login">Sign in</NavLink>
          )}
        </div>
      </nav>

      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/"       element={user ? <PlannerPage />    : <LoginPage />} />
        <Route path="/trips"  element={user ? <TripsPage />      : <LoginPage />} />
        <Route path="/trips/:id" element={user ? <TripDetailPage /> : <LoginPage />} />
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <UserProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </UserProvider>
  )
}
