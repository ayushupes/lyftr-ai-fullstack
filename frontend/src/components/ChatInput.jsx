import React, { useState } from 'react'

export default function ChatInput({ onSendMessage, isLoading }) {
  const [text, setText] = useState('')

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return
    onSendMessage(trimmed)
    setText('') // Empty after sending (strict requirement)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      borderTop: '1px solid #334155',
      backgroundColor: '#1e293b',
      padding: '1rem 1.5rem'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'flex-end'
      }}>
        <textarea
          data-testid="chat-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          disabled={isLoading}
          rows={1}
          style={{
            flex: 1,
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            border: '1px solid #475569',
            borderRadius: '12px',
            padding: '0.75rem 1rem',
            fontSize: '0.92rem',
            lineHeight: '1.4',
            resize: 'none',
            fontFamily: 'inherit',
            outline: 'none',
            maxHeight: '120px',
            minHeight: '44px'
          }}
        />

        <button
          data-testid="send-button"
          type="button"
          onClick={handleSend}
          disabled={isLoading || !text.trim()}
          style={{
            backgroundColor: isLoading || !text.trim() ? '#334155' : '#2563eb',
            color: isLoading || !text.trim() ? '#64748b' : '#ffffff',
            border: 'none',
            borderRadius: '12px',
            padding: '0 1.25rem',
            height: '44px',
            fontSize: '0.92rem',
            fontWeight: 600,
            cursor: isLoading || !text.trim() ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.15s',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.4rem',
            whiteSpace: 'nowrap'
          }}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
