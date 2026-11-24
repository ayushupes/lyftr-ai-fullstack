import React, { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import SystemPromptModal from './components/SystemPromptModal'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'

// Generate a random client session ID: e.g. s-7f3a...
function generateSessionId() {
  const rand = Math.random().toString(36).substring(2, 8)
  return `s-${rand}`
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function App() {
  const [sessionId, setSessionId] = useState(() => generateSessionId())
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [health, setHealth] = useState(null)
  const [systemPrompt, setSystemPrompt] = useState('')
  const [showSystemPrompt, setShowSystemPrompt] = useState(false)
  const [simulationHeader, setSimulationHeader] = useState('')

  // Poll or check health on initial load
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/health`)
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      } else {
        setHealth(null)
      }
    } catch {
      setHealth(null)
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  // Start new session
  const handleNewSession = () => {
    const newId = generateSessionId()
    setSessionId(newId)
    setMessages([])
    setSimulationHeader('')
  }

  // Send new message
  const handleSendMessage = async (userText) => {
    if (!userText.trim() || isLoading) return

    // Append user message locally
    const userMessage = { role: 'user', content: userText }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const headers = {
        'Content-Type': 'application/json'
      }
      if (simulationHeader.trim()) {
        headers['X-Simulate-Failure'] = simulationHeader.trim()
      }

      const bodyPayload = {
        session_id: sessionId,
        message: userText
      }
      if (systemPrompt.trim()) {
        bodyPayload.system_prompt = systemPrompt.trim()
      }

      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(bodyPayload)
      })

      const data = await response.json()

      if (!response.ok) {
        // Handle 422, 503 or other server errors
        let errorDetail = 'An error occurred'
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorDetail = data.detail
          } else if (Array.isArray(data.detail)) {
            errorDetail = data.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
          } else {
            errorDetail = JSON.stringify(data.detail)
          }
        }
        setMessages((prev) => [
          ...prev,
          {
            role: 'error',
            title: `HTTP ${response.status}`,
            content: errorDetail
          }
        ])
      } else {
        // Successful response: append assistant message with metadata
        const assistantMessage = {
          role: 'assistant',
          content: data.reply,
          metadata: data.metadata
        }
        setMessages((prev) => [...prev, assistantMessage])
      }
    } catch (err) {
      // Network or connection error
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          title: 'Network / Connection Error',
          content: `Unable to reach backend gateway at ${API_BASE}. Make sure the backend server is running.`
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: '#0f172a',
      color: '#f8fafc'
    }}>
      <Header
        sessionId={sessionId}
        health={health}
        systemPrompt={systemPrompt}
        setSystemPrompt={setSystemPrompt}
        showSystemPrompt={showSystemPrompt}
        setShowSystemPrompt={setShowSystemPrompt}
        simulationHeader={simulationHeader}
        setSimulationHeader={setSimulationHeader}
        onNewSession={handleNewSession}
      />

      <SystemPromptModal
        systemPrompt={systemPrompt}
        setSystemPrompt={setSystemPrompt}
        isOpen={showSystemPrompt}
        onClose={() => setShowSystemPrompt(false)}
      />

      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        maxWidth: '900px',
        width: '100%',
        margin: '0 auto',
        height: '100%'
      }}>
        <MessageList messages={messages} isLoading={isLoading} />
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </main>
    </div>
  )
}
