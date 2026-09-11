import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../hooks/useUser'
import { getTrips, deleteTrip } from '../api/client'
import dayjs from 'dayjs'

const TRIP_ICONS = ['🗼', '🏯', '🗽', '🏖️', '🏔️', '🌅', '🏛️', '🌍', '🎭', '🧳']

export default function TripsPage() {
  const { user } = useUser()
  const navigate = useNavigate()
  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getTrips(user.id)
      .then(r => setTrips(r.data))
      .catch(() => setError('Failed to load trips.'))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!confirm('Delete this trip?')) return
    await deleteTrip(id)
    setTrips(p => p.filter(t => t.id !== id))
  }

  if (loading) return <div className="spinner-wrap"><div className="spinner" /></div>

  return (
    <div className="page">
      <div className="page-hero">
        <h1 className="page-title">My Trips</h1>
        <p className="page-subtitle">{trips.length} saved itinerar{trips.length === 1 ? 'y' : 'ies'} — click any to view or refine</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {trips.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🗺️</div>
          <h3>No trips yet</h3>
          <p>Head over to <a href="/">Plan Trip</a> to generate your first AI itinerary!</p>
        </div>
      ) : (
        <div className="trip-grid">
          {trips.map((t, i) => {
            const numDays = dayjs(t.end_date).diff(dayjs(t.start_date), 'day') + 1
            const icon = TRIP_ICONS[t.id % TRIP_ICONS.length]
            return (
              <div key={t.id} className="trip-card" onClick={() => navigate(`/trips/${t.id}`)}>
                <div className="trip-card-icon">{icon}</div>
                <div className="trip-card-info">
                  <h4>{t.title}</h4>
                  <small>
                    📍 {t.destination} &nbsp;·&nbsp;
                    📅 {dayjs(t.start_date).format('MMM D')} – {dayjs(t.end_date).format('MMM D, YYYY')} &nbsp;·&nbsp;
                    {numDays} day{numDays !== 1 ? 's' : ''} &nbsp;·&nbsp;
                    👥 {t.num_travelers} traveler{t.num_travelers > 1 ? 's' : ''}
                  </small>
                </div>
                <div className="trip-card-actions" onClick={e => e.stopPropagation()}>
                  <button className="btn btn-sm btn-primary" onClick={() => navigate(`/trips/${t.id}`)}>View</button>
                  <button className="btn btn-sm btn-danger" onClick={e => handleDelete(t.id, e)}>Delete</button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
