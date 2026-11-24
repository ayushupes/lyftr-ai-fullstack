import React, { useEffect, useRef } from 'react'
import MessageItem from './MessageItem'

export default function MessageList({ messages, isLoading }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div style={{
      flex: 1,
      overflowY: 'auto',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {messages.length === 0 ? (
        <div style={{
          margin: 'auto',
          textAlign: 'center',
          maxWidth: '480px',
          color: '#64748b',
          padding: '2rem 1rem'
        }}>
          <div style={{
            fontSize: '2.5rem',
            marginBottom: '0.75rem',
            filter: 'grayscale(0.3)'
          }}>
            ⚡
          </div>
          <h2 style={{ fontSize: '1.15rem', color: '#e2e8f0', marginBottom: '0.5rem', fontWeight: 600 }}>
            Start a Conversation
          </h2>
          <p style={{ fontSize: '0.88rem', lineHeight: '1.5' }}>
            Send a query below. Responses feature automatic key failover across provider rate-limits (429/5xx) and built-in LiteLLM caching.
          </p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageItem key={index} message={msg} />
        ))
      )}

      {/* Loading typing indicator */}
      {isLoading && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          backgroundColor: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '16px',
          padding: '0.6rem 1rem',
          width: 'fit-content',
          marginBottom: '1rem',
          animation: 'fadeIn 0.2s ease-out'
        }}>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Thinking</span>
          <span style={{ display: 'flex', gap: '3px' }}>
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#60a5fa', animation: 'pulse 1s infinite' }} />
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#60a5fa', animation: 'pulse 1s infinite 0.2s' }} />
            <span style={{ width: '5px', height: '5px', borderRadius: '50%', backgroundColor: '#60a5fa', animation: 'pulse 1s infinite 0.4s' }} />
          </span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
