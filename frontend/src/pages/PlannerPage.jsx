import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../hooks/useUser'
import { generateItinerary } from '../api/client'
import ItineraryDisplay from '../components/ItineraryDisplay'
import dayjs from 'dayjs'

const INTERESTS = [
  { label: '🏔️ Adventure', value: 'Adventure' },
  { label: '🏛️ Culture', value: 'Culture' },
  { label: '🍜 Food', value: 'Food' },
  { label: '🧘 Relaxation', value: 'Relaxation' },
  { label: '🌿 Nature', value: 'Nature' },
  { label: '🎨 Art', value: 'Art' },
  { label: '🎉 Nightlife', value: 'Nightlife' },
  { label: '🏖️ Beach', value: 'Beach' },
  { label: '📜 History', value: 'History' },
  { label: '🛍️ Shopping', value: 'Shopping' },
  { label: '🦁 Wildlife', value: 'Wildlife' },
  { label: '🏗️ Architecture', value: 'Architecture' },
]

const DEFAULT_FORM = {
  destination: '',
  start_date: dayjs().add(14, 'day').format('YYYY-MM-DD'),
  end_date: dayjs().add(18, 'day').format('YYYY-MM-DD'),
  budget_min: '',
  budget_max: '',
  num_travelers: 1,
  interests: [],
  save: true,
}

export default function PlannerPage() {
  const { user } = useUser()
  const navigate = useNavigate()
  const [form, setForm] = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const toggleInterest = (v) =>
    setForm(p => ({ ...p, interests: p.interests.includes(v) ? p.interests.filter(x => x !== v) : [...p.interests, v] }))

  const surpriseMe = () => setForm(p => ({ ...p, destination: 'surprise me' }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const res = await generateItinerary({
        ...form,
        user_id: user.id,
        budget_min: form.budget_min ? parseFloat(form.budget_min) : null,
        budget_max: form.budget_max ? parseFloat(form.budget_max) : null,
        num_travelers: parseInt(form.num_travelers),
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate itinerary. Is the backend running?')
    } finally { setLoading(false) }
  }

  return (
    <div className="page">
      {/* Hero */}
      <div className="page-hero">
        <h1 className="page-title">Plan Your Perfect Trip</h1>
        <p className="page-subtitle">Tell us where you want to go — IBM Granite builds your day-by-day itinerary</p>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <form onSubmit={handleSubmit}>

          {/* Destination */}
          <div className="section-heading">📍 Where are you going?</div>
          <div className="form-group">
            <label className="form-label">Destination</label>
            <div className="dest-input-wrap">
              <input
                className="form-input"
                value={form.destination}
                onChange={e => setForm(p => ({ ...p, destination: e.target.value }))}
                placeholder='e.g. "Tokyo, Japan" or "Bali" or try Surprise Me!'
                required
              />
              <button type="button" className="surprise-btn" onClick={surpriseMe}>
                🎲 Surprise Me!
              </button>
            </div>
          </div>

          {/* Dates */}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input type="date" className="form-input"
                value={form.start_date} min={dayjs().format('YYYY-MM-DD')}
                onChange={e => setForm(p => ({ ...p, start_date: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="form-label">End Date</label>
              <input type="date" className="form-input"
                value={form.end_date} min={form.start_date}
                onChange={e => setForm(p => ({ ...p, end_date: e.target.value }))} required />
            </div>
          </div>

          {/* Budget & Travelers */}
          <div className="section-heading" style={{ marginTop: '.5rem' }}>💰 Budget & Travelers</div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Budget Range (₹ INR total)</label>
              <div style={{ display: 'flex', gap: '.5rem', alignItems: 'center' }}>
                <input type="number" className="form-input" placeholder="Min ₹" min={0}
                  value={form.budget_min} onChange={e => setForm(p => ({ ...p, budget_min: e.target.value }))} />
                <span style={{ color: 'var(--text3)', flexShrink: 0, fontWeight: 700 }}>–</span>
                <input type="number" className="form-input" placeholder="Max ₹" min={0}
                  value={form.budget_max} onChange={e => setForm(p => ({ ...p, budget_max: e.target.value }))} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Travelers</label>
              <input type="number" className="form-input" min={1} max={20}
                value={form.num_travelers} onChange={e => setForm(p => ({ ...p, num_travelers: e.target.value }))} />
            </div>
          </div>

          {/* Interests */}
          <div className="section-heading" style={{ marginTop: '.5rem' }}>🎯 Your Interests</div>
          <div className="form-group">
            <div className="tags-group">
              {INTERESTS.map(({ label, value }) => (
                <button key={value} type="button"
                  className={`tag-btn ${form.interests.includes(value) ? 'selected' : ''}`}
                  onClick={() => toggleInterest(value)}>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Save toggle */}
          <label className="save-toggle">
            <input type="checkbox" checked={form.save}
              onChange={e => setForm(p => ({ ...p, save: e.target.checked }))} />
            <span className="save-toggle-track">
              <span className="save-toggle-thumb" />
            </span>
            <span className="save-toggle-label">
              {form.save ? '💾 Save this trip to My Trips' : '🚫 Don\'t save — just preview'}
            </span>
          </label>

          {error && <div className="alert alert-error" style={{ marginTop: '1rem' }}>{error}</div>}

          <button className="btn btn-primary btn-full btn-lg" disabled={loading} style={{ marginTop: '.85rem' }}>
            {loading
              ? <><span className="spinner" style={{ width: 20, height: 20, borderWidth: 2, borderTopColor: '#fff' }} /> Generating…</>
              : '✈️ Generate My Itinerary'}
          </button>
        </form>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="generating-card">
          <div className="spinner" />
          <p><strong>IBM Granite</strong> is crafting your personalised itinerary…</p>
          <p style={{ marginTop: '.35rem', fontSize: '.78rem' }}>Retrieving destination knowledge · Building day-by-day plan</p>
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <ItineraryDisplay
          result={result}
          onViewTrip={() => result.trip_id && navigate(`/trips/${result.trip_id}`)}
        />
      )}
    </div>
  )
}
