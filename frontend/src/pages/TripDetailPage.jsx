import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getTrip, refineItinerary } from '../api/client'
import ItineraryDisplay from '../components/ItineraryDisplay'
import dayjs from 'dayjs'

export default function TripDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [trip, setTrip] = useState(null)
  const [itinerary, setItinerary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refining, setRefining] = useState(false)
  const [chatMsg, setChatMsg] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    getTrip(id)
      .then(res => {
        setTrip(res.data)
        setItinerary({ trip_id: res.data.id, itinerary: buildDays(res.data.items), sources: [] })
      })
      .catch(() => setError('Trip not found.'))
      .finally(() => setLoading(false))
  }, [id])

  const handleRefine = async (e) => {
    e.preventDefault()
    if (!chatMsg.trim()) return
    setError('')
    setRefining(true)
    try {
      const res = await refineItinerary({ trip_id: parseInt(id), user_message: chatMsg })
      setItinerary(res.data)
      setChatMsg('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Refinement failed.')
    } finally { setRefining(false) }
  }

  if (loading) return <div className="spinner-wrap"><div className="spinner" /></div>
  if (error && !trip) return (
    <div className="page">
      <div className="alert alert-error">{error}</div>
      <button className="btn btn-secondary btn-sm" onClick={() => navigate('/trips')}>← Back to Trips</button>
    </div>
  )

  const numDays = trip ? dayjs(trip.end_date).diff(dayjs(trip.start_date), 'day') + 1 : 0

  return (
    <div className="page">
      {/* Back + header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/trips')} style={{ marginTop: '.25rem' }}>
          ← Back
        </button>
        <div>
          <h1 className="page-title" style={{ fontSize: '1.4rem' }}>{trip?.title}</h1>
          <p className="page-subtitle">
            📍 {trip?.destination} &nbsp;·&nbsp;
            📅 {dayjs(trip?.start_date).format('MMM D')} – {dayjs(trip?.end_date).format('MMM D, YYYY')} &nbsp;·&nbsp;
            {numDays} days &nbsp;·&nbsp;
            👥 {trip?.num_travelers} traveler{trip?.num_travelers > 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {itinerary && <ItineraryDisplay result={itinerary} />}

      {/* Chat refinement */}
      <div className="chat-box">
        <h3>💬 Refine with AI</h3>
        <p>Ask IBM Granite to modify specific days, add food stops, change the pace, or anything else.</p>
        {error && <div className="alert alert-error">{error}</div>}
        {refining && (
          <div className="generating-card" style={{ marginBottom: '1rem', padding: '1.25rem' }}>
            <div className="spinner" style={{ width: 28, height: 28 }} />
            <p style={{ marginTop: '.5rem' }}><strong>IBM Granite</strong> is refining your itinerary…</p>
          </div>
        )}
        <form onSubmit={handleRefine}>
          <div className="chat-input-row">
            <input
              className="form-input"
              value={chatMsg}
              onChange={e => setChatMsg(e.target.value)}
              placeholder='e.g. "Make day 2 more relaxed" · "Add more food stops on day 3" · "Day 1 is too busy"'
              disabled={refining}
            />
            <button type="submit" className="chat-send-btn" disabled={refining || !chatMsg.trim()}>
              {refining ? '⏳' : '✦ Refine'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function buildDays(items = []) {
  const map = {}
  for (const item of items) {
    if (!map[item.day_number]) map[item.day_number] = { day: item.day_number }
    map[item.day_number][item.period] = {
      activity: item.activity, location: item.location,
      description: item.description, estimated_cost: item.estimated_cost,
      weather_risk: item.weather_risk, tips: item.tips,
    }
  }
  return Object.values(map).sort((a, b) => a.day - b.day)
}
