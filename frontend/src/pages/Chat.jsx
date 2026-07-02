import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import api, { API_URL } from '../api'
import { useAuth } from '../context/AuthContext'

const WS_URL = import.meta.env.VITE_WS_URL || API_URL.replace(/^http/, 'ws')

export default function Chat() {
  const { interestId } = useParams()
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState('')
  const wsRef = useRef(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    // Load message history first, then open the live connection
    api.get(`/interests/${interestId}/messages`)
      .then((res) => setMessages(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Could not load chat'))

    const token = localStorage.getItem('token')
    const ws = new WebSocket(`${WS_URL}/ws/chat/${interestId}?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setError('Connection error - chat may only be available once interest is accepted')
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setMessages((prev) => [...prev, data])
    }

    return () => ws.close()
  }, [interestId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function sendMessage(e) {
    e.preventDefault()
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ content: input }))
    setInput('')
  }

  return (
    <div className="page chat-page">
      <h2>Chat</h2>
      <p className="connection-status">{connected ? '🟢 Connected' : '🔴 Disconnected'}</p>
      {error && <p className="error">{error}</p>}

      <div className="chat-window">
        {messages.map((m) => (
          <div key={m.id} className={`chat-bubble ${m.sender_id === user.id ? 'mine' : 'theirs'}`}>
            <p>{m.content}</p>
            <span className="chat-time">{new Date(m.sent_at).toLocaleTimeString()}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={sendMessage} className="chat-input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={!connected}
        />
        <button type="submit" disabled={!connected}>Send</button>
      </form>
    </div>
  )
}