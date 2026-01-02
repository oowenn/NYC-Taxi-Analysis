import { useState, useRef, useEffect } from 'react'
import { Turnstile } from '@marsidev/react-turnstile'
import MessageList from './MessageList'
import { sendMessage } from '../api/chat'
import './ChatInterface.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || ''

const getApiPath = (endpoint: string) => {
  if (API_URL.startsWith('/')) {
    return `${API_URL}${endpoint}`
  } else {
    return `${API_URL}/api${endpoint}`
  }
}
// Detect dev mode: localhost, 127.0.0.1, or /api (Vite proxy)
const isDevMode = API_URL.includes('localhost') || API_URL.includes('127.0.0.1') || API_URL === '/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sql?: string
  data?: any[]
  data_preview?: any[]
  chart?: any
  chart_image_url?: string
  sources?: string[]
  mode?: string
  cached?: boolean
}

type LoadingStage = 'idle' | 'generating-sql' | 'fetching-data' | 'generating-visualization'

export default function ChatInterface() {
  // Initialize with welcome message from assistant
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Welcome! 👋\n\nTry asking:\n• "Top 10 pickup zones"\n• "What is the percentage of base passenger fares held by each company?"\n• "Show hourly trips by company for the first 3 days of January 2023"\n• "What do the trip miles by company over time look like?"'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState<LoadingStage>('idle')
  const [turnstileToken, setTurnstileToken] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [previewData, setPreviewData] = useState<any>(null)
  const [previewLoading, setPreviewLoading] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const stageTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Fetch preview data on mount
  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const response = await fetch(getApiPath('/data-preview'))
        if (response.ok) {
          const data = await response.json()
          setPreviewData(data)
        }
      } catch (err) {
        // Silently fail - preview is optional
      } finally {
        setPreviewLoading(false)
      }
    }
    fetchPreview()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // In dev mode, allow submission even without Turnstile token
    if (!input.trim() || loading || (!turnstileToken && !isDevMode)) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')
    
    // Clear any existing timer
    if (stageTimerRef.current) {
      clearTimeout(stageTimerRef.current)
    }
    
    // Progress through loading stages
    // Start with SQL generation
    setLoadingStage('generating-sql')
    
    // Move to "fetching-data" after a short delay (SQL generation typically takes longer)
    stageTimerRef.current = setTimeout(() => {
      setLoadingStage('fetching-data')
    }, 3000) // Give SQL generation 3 seconds before showing "fetching data"

    try {
      // Use a dummy token in dev mode if Turnstile hasn't provided one
      const token = turnstileToken || (isDevMode ? 'dev-token' : '')
      const response = await sendMessage(input.trim(), token)
      
      // Only show "generating-visualization" if we actually get a chart in the response
      // or if we've been waiting long enough (chart generation happens after data fetch)
      if (response.chart || response.chart_image_url) {
        setLoadingStage('generating-visualization')
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sql: response.sql,
        data: response.data,
        data_preview: response.data_preview,
        chart: response.chart,
        chart_image_url: response.chart_image_url,
        sources: response.sources,
        mode: response.mode,
        cached: response.cached
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err: any) {
      setError(err.message || 'Failed to send message')
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to process your request'}`,
        mode: 'error'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      setLoadingStage('idle')
      if (stageTimerRef.current) {
        clearTimeout(stageTimerRef.current)
        stageTimerRef.current = null
      }
      setTurnstileToken('') // Reset token after use
    }
  }

  return (
    <div className="chat-interface">
      <MessageList 
        messages={messages} 
        loading={loading}
        loadingStage={loadingStage}
        onShowSQL={(message) => console.log('SQL:', message.sql)}
        previewData={previewData}
        previewLoading={previewLoading}
      />
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit} className="chat-input-form">
        {!isDevMode && (
          <div className="turnstile-container">
            <Turnstile
              siteKey={TURNSTILE_SITE_KEY || '1x00000000000000000000AA'} // Demo key if not set
              onSuccess={(token) => {
                setTurnstileToken(token)
                setError('') // Clear any previous errors
              }}
              onError={() => {
                setError('Turnstile verification failed')
              }}
              options={{
                theme: 'light',
                size: 'normal'
              }}
            />
          </div>
        )}
        
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="ASK about NYC Uber/Lyft trip data..."
            disabled={loading}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="send-button"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
      
      <div ref={messagesEndRef} />
    </div>
  )
}

