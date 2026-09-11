import React, { useState } from 'react'
import dayjs from 'dayjs'

const SLOT_CONFIG = {
  morning:   { icon: '🌅', label: 'Morning',   cls: 'slot-morning'   },
  afternoon: { icon: '☀️',  label: 'Afternoon', cls: 'slot-afternoon' },
  evening:   { icon: '🌙', label: 'Evening',   cls: 'slot-evening'   },
}

// Rotate gradient colours across day cards
const HEADER_GRADIENTS = [
  'linear-gradient(135deg,#6366f1,#8b5cf6)',
  'linear-gradient(135deg,#8b5cf6,#ec4899)',
  'linear-gradient(135deg,#ec4899,#f59e0b)',
  'linear-gradient(135deg,#10b981,#6366f1)',
  'linear-gradient(135deg,#f59e0b,#ef4444)',
  'linear-gradient(135deg,#3b82f6,#10b981)',
  'linear-gradient(135deg,#a855f7,#ec4899)',
]

function Slot({ period, slot }) {
  if (!slot?.activity) return null
  const { icon, label, cls } = SLOT_CONFIG[period]
  const cost = slot.estimated_cost
  const risk = slot.weather_risk?.toLowerCase() || 'low'

  return (
    <div className={`slot ${cls}`}>
      <div className="slot-period">
        <span className="slot-period-icon">{icon}</span>
        <span className="slot-period-label">{label}</span>
      </div>
      <div className="slot-content">
        <div className="slot-activity">{slot.activity}</div>
        {slot.location && (
          <div className="slot-location">
            <span>📍</span>{slot.location}
          </div>
        )}
        {slot.description && <div className="slot-desc">{slot.description}</div>}
        <div className="slot-meta">
          {cost > 0
            ? <span className="badge badge-cost">💰 ₹{cost.toLocaleString('en-IN')}/person</span>
            : <span className="badge badge-free">✓ Free</span>
          }
          {risk === 'high'   && <span className="badge badge-risk-high">⚠️ Rain Risk</span>}
          {risk === 'medium' && <span className="badge badge-risk-medium">🌂 Some Risk</span>}
        </div>
        {slot.tips && <div className="slot-tips">💡 {slot.tips}</div>}
      </div>
    </div>
  )
}

export default function DayCard({ day, index = 0 }) {
  const [open, setOpen] = useState(true)

  const dayCost = ['morning', 'afternoon', 'evening']
    .reduce((s, p) => s + (day[p]?.estimated_cost || 0), 0)

  const gradient = HEADER_GRADIENTS[index % HEADER_GRADIENTS.length]

  const dateLabel = day.date
    ? dayjs(day.date).format('dddd, MMM D')
    : `Day ${day.day}`

  return (
    <div className="day-card">
      <div className="day-header" style={{ background: gradient }} onClick={() => setOpen(o => !o)}>
        <div>
          <div className="day-number">Day {day.day}</div>
          <div className="day-title">{dateLabel}</div>
        </div>
        <div className="day-header-right">
          {dayCost > 0 && <span className="day-cost-badge">~₹{dayCost.toLocaleString('en-IN')}</span>}
          <span className="day-toggle">{open ? '▲' : '▼'}</span>
        </div>
      </div>
      {open && (
        <div className="day-body">
          <Slot period="morning"   slot={day.morning} />
          <Slot period="afternoon" slot={day.afternoon} />
          <Slot period="evening"   slot={day.evening} />
        </div>
      )}
    </div>
  )
}
