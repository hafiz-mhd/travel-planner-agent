import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../hooks/useUser'
import { createUser, getUser } from '../api/client'

export default function LoginPage() {
  const { login } = useUser()
  const navigate = useNavigate()
  const [tab, setTab] = useState('create')
  const [form, setForm] = useState({ name: '', email: '' })
  const [userId, setUserId] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await createUser(form)
      login(res.data)
      navigate('/')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail === 'Email already registered') {
        setError('That email is already registered. Switch to "Sign In" and enter your User ID.')
      } else {
        setError(detail || 'Could not create account. Is the backend running?')
      }
    } finally { setLoading(false) }
  }

  const handleLookup = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await getUser(parseInt(userId))
      login(res.data)
      navigate('/')
    } catch {
      setError('User ID not found. Check your ID or create a new account.')
    } finally { setLoading(false) }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Dark top section */}
        <div className="login-top">
          <span className="login-emoji">✈️</span>
          <div className="login-title">Travel Planner Agent</div>
          <div className="login-sub">AI-powered itineraries · IBM Granite · RAG</div>
        </div>

        {/* White body */}
        <div className="login-body">
        {/* Tabs */}
        <div className="tab-row">
          <button className={`tab-btn ${tab === 'create' ? 'active' : ''}`} onClick={() => { setTab('create'); setError('') }}>
            ✨ Create Account
          </button>
          <button className={`tab-btn ${tab === 'login' ? 'active' : ''}`} onClick={() => { setTab('login'); setError('') }}>
            🔑 Sign In
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {tab === 'create' ? (
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label className="form-label">Your Name</label>
              <input
                className="form-input"
                value={form.name}
                onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                placeholder="e.g. Alex Johnson"
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                value={form.email}
                onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                placeholder="you@example.com"
                required
              />
            </div>
            <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: '.25rem' }} disabled={loading}>
              {loading
                ? <><span className="spinner" style={{ width: 18, height: 18, borderWidth: 2, borderTopColor: '#fff' }} /> Creating…</>
                : '🚀 Create Account & Start Planning'}
            </button>
            <p style={{ textAlign: 'center', fontSize: '.78rem', color: 'var(--text3)', marginTop: '1rem' }}>
              Your User ID is shown after creation — keep it to sign in again.
            </p>
          </form>
        ) : (
          <form onSubmit={handleLookup}>
            <div className="form-group">
              <label className="form-label">User ID</label>
              <input
                type="number"
                className="form-input"
                value={userId}
                onChange={e => setUserId(e.target.value)}
                placeholder="Enter your numeric user ID"
                required
                autoFocus
                min="1"
              />
            </div>
            <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: '.25rem' }} disabled={loading}>
              {loading
                ? <><span className="spinner" style={{ width: 18, height: 18, borderWidth: 2, borderTopColor: '#fff' }} /> Signing in…</>
                : '✈️ Sign In'}
            </button>
          </form>
        )}

        {/* Features list */}
        <div className="feature-list">
          <div className="feature-list-header">What you get</div>
          {[
            ['🗺️', 'Day-by-day itineraries with IBM Granite AI'],
            ['📚', 'RAG-grounded from real destination data'],
            ['🌤️', 'Weather-aware activity planning'],
            ['💬', 'Chat refinement · Budget in ₹ INR'],
          ].map(([icon, text]) => (
            <div key={text} className="feature-item">
              <span className="feature-icon">{icon}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>
        </div>{/* end login-body */}
      </div>
    </div>
  )
}
