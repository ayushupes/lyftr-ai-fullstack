import React from 'react'

export default function SystemPromptModal({
  systemPrompt,
  setSystemPrompt,
  isOpen,
  onClose
}) {
  if (!isOpen) return null

  return (
    <div style={{
      backgroundColor: '#1e293b',
      borderBottom: '1px solid #334155',
      padding: '1rem 1.5rem',
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0' }}>
            System Prompt (Optional - applies to this session):
          </label>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            ✕ Close
          </button>
        </div>
        <textarea
          data-testid="system-prompt-input"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="e.g. You are a senior Python software architect. Answer concisely."
          rows={3}
          style={{
            width: '100%',
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            border: '1px solid #475569',
            borderRadius: '8px',
            padding: '0.6rem 0.8rem',
            fontSize: '0.85rem',
            resize: 'vertical',
            fontFamily: 'inherit',
            outline: 'none'
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', fontSize: '0.75rem', color: '#64748b' }}>
          <span>Overrides default system prompt for new queries in this session.</span>
          {systemPrompt && (
            <button
              type="button"
              onClick={() => setSystemPrompt('')}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#f43f5e',
                cursor: 'pointer',
                fontSize: '0.75rem'
              }}
            >
              Clear prompt
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
