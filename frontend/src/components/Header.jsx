import React from 'react'

export default function Header({
  sessionId,
  health,
  systemPrompt,
  setSystemPrompt,
  showSystemPrompt,
  setShowSystemPrompt,
  simulationHeader,
  setSimulationHeader,
  onNewSession
}) {
  return (
    <header style={{
      backgroundColor: '#1e293b',
      borderBottom: '1px solid #334155',
      padding: '0.75rem 1.5rem',
      display: 'flex',
      flexWrap: 'wrap',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '1rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          color: '#ffffff'
        }}>
          L
        </div>
        <div>
          <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', lineHeight: 1.2 }}>
            Lyftr AI Chatbot
          </h1>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Multi-Key Failover &amp; LiteLLM Cache Gateway
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        {/* Health status badge */}
        <div style={{
          fontSize: '0.75rem',
          padding: '0.25rem 0.6rem',
          borderRadius: '9999px',
          backgroundColor: health?.status === 'ok' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          color: health?.status === 'ok' ? '#34d399' : '#f87171',
          border: `1px solid ${health?.status === 'ok' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem'
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: health?.status === 'ok' ? '#10b981' : '#ef4444'
          }} />
          {health ? `Ready (${health.keys_configured} keys | Cache: on)` : 'Connecting...'}
        </div>

        {/* Current session indicator */}
        <div style={{
          fontSize: '0.75rem',
          color: '#cbd5e1',
          backgroundColor: '#0f172a',
          padding: '0.25rem 0.6rem',
          borderRadius: '6px',
          border: '1px solid #334155'
        }}>
          Session: <code style={{ color: '#38bdf8' }}>{sessionId}</code>
        </div>

        {/* Failover simulation dropdown (test hook helper) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem' }}>
          <label style={{ color: '#94a3b8' }}>Simulate:</label>
          <select
            value={simulationHeader}
            onChange={(e) => setSimulationHeader(e.target.value)}
            style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              border: '1px solid #334155',
              borderRadius: '6px',
              padding: '0.25rem 0.5rem',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            <option value="">None (Normal)</option>
            <option value="key_1=429">key_1=429 (Trigger key_2 fallback)</option>
            <option value="key_1=500">key_1=500 (Trigger key_2 fallback)</option>
            <option value="*=429">*=429 (Simulate all fail -&gt; 503)</option>
          </select>
        </div>

        {/* Toggle System Prompt Modal/Drawer */}
        <button
          type="button"
          onClick={() => setShowSystemPrompt(!showSystemPrompt)}
          style={{
            backgroundColor: showSystemPrompt ? '#334155' : '#0f172a',
            color: '#94a3b8',
            border: '1px solid #334155',
            borderRadius: '6px',
            padding: '0.35rem 0.65rem',
            fontSize: '0.75rem',
            cursor: 'pointer',
            transition: 'all 0.15s'
          }}
        >
          {systemPrompt ? '⚙️ Prompt set' : '⚙️ System Prompt'}
        </button>

        {/* New Session Button */}
        <button
          type="button"
          onClick={onNewSession}
          style={{
            backgroundColor: '#2563eb',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            padding: '0.35rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          + New Chat
        </button>
      </div>
    </header>
  )
}
