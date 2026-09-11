import React from 'react'
import DayCard from './DayCard'

export default function ItineraryDisplay({ result, onViewTrip }) {
  if (!result) return null
  const { itinerary = [], weather_summary, sources = [], trip_id, summary, title } = result

  const totalCost = itinerary.reduce((sum, day) => {
    return sum + ['morning', 'afternoon', 'evening'].reduce((s, p) => s + (day[p]?.estimated_cost || 0), 0)
  }, 0)

  const numDays = itinerary.length
  const totalActivities = itinerary.reduce((n, day) =>
    n + ['morning','afternoon','evening'].filter(p => day[p]?.activity).length, 0)

  return (
    <div>
      {/* Itinerary header banner */}
      <div className="itinerary-header">
        <h2>{title || 'Your Itinerary is Ready!'} 🎉</h2>
        <p>{summary || "Here's your personalised day-by-day plan powered by IBM Granite"}</p>
      </div>

      {/* Stats row */}
      <div className="summary-stats">
        <div className="stat-chip">
          <div className="stat-chip-val">{numDays}</div>
          <div className="stat-chip-lbl">Days</div>
        </div>
        <div className="stat-chip">
          <div className="stat-chip-val">{totalActivities}</div>
          <div className="stat-chip-lbl">Activities</div>
        </div>
        {totalCost > 0 && (
          <div className="stat-chip">
            <div className="stat-chip-val">₹{totalCost.toLocaleString('en-IN')}</div>
            <div className="stat-chip-lbl">Est. Total</div>
          </div>
        )}
        {totalCost > 0 && numDays > 0 && (
          <div className="stat-chip">
            <div className="stat-chip-val">₹{Math.round(totalCost / numDays).toLocaleString('en-IN')}</div>
            <div className="stat-chip-lbl">Per Day</div>
          </div>
        )}
      </div>

      {/* Weather */}
      {weather_summary && (
        <div className="weather-banner">
          <span className="weather-icon">🌤️</span>
          <span>{weather_summary}</span>
        </div>
      )}

      {/* Day cards */}
      {itinerary.map((day, i) => <DayCard key={i} day={day} index={i} />)}

      {/* Sources */}
      {sources.length > 0 && (
        <div className="sources">
          <span>📚 Knowledge sources:</span>
          {[...new Set(sources)].map((s, i) => <span key={i} className="source-chip">{s}</span>)}
        </div>
      )}

      {/* Action buttons */}
      <div style={{ marginTop: '1.25rem', display: 'flex', gap: '.75rem', flexWrap: 'wrap' }}>
        {trip_id && onViewTrip && (
          <>
            <button className="btn btn-primary" onClick={onViewTrip}>
              💬 Refine with AI
            </button>
            <button className="btn btn-secondary" onClick={onViewTrip}>
              📋 View Full Trip
            </button>
          </>
        )}
        {!trip_id && (
          <div className="alert alert-info" style={{ margin: 0 }}>
            ℹ️ This itinerary was not saved. Enable "Save trip" on the form to persist it.
          </div>
        )}
      </div>
    </div>
  )
}
