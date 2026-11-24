import React from 'react'

export default function MessageItem({ message }) {
  if (message.role === 'user') {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'flex-end',
        marginBottom: '1rem',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        <div style={{
          maxWidth: '75%',
          backgroundColor: '#2563eb',
          color: '#ffffff',
          borderRadius: '16px 16px 4px 16px',
          padding: '0.75rem 1rem',
          fontSize: '0.92rem',
          lineHeight: '1.5',
          wordBreak: 'break-word',
          boxShadow: '0 2px 4px rgba(0,0,0,0.15)'
        }}>
          {message.content}
        </div>
      </div>
    )
  }

  if (message.role === 'error') {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'flex-start',
        marginBottom: '1rem',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        <div style={{
          maxWidth: '85%',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#fca5a5',
          borderRadius: '12px',
          padding: '0.75rem 1rem',
          fontSize: '0.88rem',
          lineHeight: '1.4'
        }}>
          <div style={{ fontWeight: 600, marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span>⚠️</span> Error: {message.title || 'Request Failed'}
          </div>
          <div>{message.content}</div>
        </div>
      </div>
    )
  }

  // Assistant Message Container
  const meta = message.metadata || {}
  const isCache = meta.resolution_source === 'LLM_CACHE'

  return (
    <div
      data-testid="assistant-message"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        marginBottom: '1.25rem',
        animation: 'fadeIn 0.2s ease-out',
        maxWidth: '85%'
      }}
    >
      {/* Assistant Text Bubble */}
      <div style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        color: '#f8fafc',
        borderRadius: '16px 16px 16px 4px',
        padding: '0.85rem 1.15rem',
        fontSize: '0.92rem',
        lineHeight: '1.55',
        wordBreak: 'break-word',
        boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
      }}>
        {message.content}
      </div>

      {/* Metadata Row */}
      {message.metadata && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '0.5rem',
          marginTop: '0.4rem',
          fontSize: '0.75rem',
          color: '#94a3b8'
        }}>
          {/* Resolution source badge */}
          <span
            data-testid="meta-source"
            style={{
              padding: '0.15rem 0.5rem',
              borderRadius: '9999px',
              fontWeight: 600,
              fontSize: '0.7rem',
              backgroundColor: isCache ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
              color: isCache ? '#34d399' : '#60a5fa',
              border: `1px solid ${isCache ? 'rgba(16, 185, 129, 0.4)' : 'rgba(59, 130, 246, 0.4)'}`
            }}
          >
            {meta.resolution_source}
          </span>

          {/* Model */}
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
            <span>Model:</span>
            <span data-testid="meta-model" style={{ color: '#e2e8f0', fontWeight: 500 }}>
              {meta.model}
            </span>
          </span>

          <span style={{ color: '#475569' }}>•</span>

          {/* Latency */}
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
            <span>Latency:</span>
            <span data-testid="meta-latency" style={{ color: '#e2e8f0', fontWeight: 500 }}>
              {meta.latency_ms} ms
            </span>
          </span>

          <span style={{ color: '#475569' }}>•</span>

          {/* Token usage */}
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
            <span>Prompt:</span>
            <span data-testid="meta-input-tokens" style={{ color: '#e2e8f0', fontWeight: 500 }}>
              {meta.input_tokens}
            </span>
          </span>

          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
            <span>Completion:</span>
            <span data-testid="meta-output-tokens" style={{ color: '#e2e8f0', fontWeight: 500 }}>
              {meta.output_tokens}
            </span>
          </span>

          {/* Key ID if present */}
          {meta.key_id && (
            <>
              <span style={{ color: '#475569' }}>•</span>
              <span style={{ color: '#cbd5e1' }}>
                Key: <code style={{ color: '#f59e0b' }}>{meta.key_id}</code>
              </span>
            </>
          )}

          {/* Fallback attempts if > 0 */}
          {meta.fallback_attempts > 0 && (
            <span style={{
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              color: '#fbbf24',
              padding: '0.1rem 0.4rem',
              borderRadius: '4px',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              fontSize: '0.7rem'
            }}>
              Failovers: {meta.fallback_attempts}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
