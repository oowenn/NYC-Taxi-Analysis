import { useState } from 'react'
import ChartRenderer from './ChartRenderer'
import DataTable from './DataTable'
import './MessageList.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sql?: string
  data?: any[]  // Full dataset for CSV
  data_preview?: any[]  // Preview for table
  chart?: any
  chart_image_url?: string
  sources?: string[]
  mode?: string
  cached?: boolean
}

type LoadingStage = 'idle' | 'generating-sql' | 'fetching-data' | 'generating-visualization'

interface MessageListProps {
  messages: Message[]
  loading: boolean
  loadingStage?: LoadingStage
  onShowSQL: (message: Message) => void
  previewData?: any
  previewLoading?: boolean
}

export default function MessageList({ messages, loading, loadingStage = 'idle', previewData, previewLoading }: MessageListProps) {
  const [expandedSQL, setExpandedSQL] = useState<Set<string>>(new Set())
  const [expandedData, setExpandedData] = useState<Set<string>>(new Set())
  const [expandedPreview, setExpandedPreview] = useState<boolean>(false)

  const toggleSQL = (messageId: string) => {
    setExpandedSQL(prev => {
      const next = new Set(prev)
      if (next.has(messageId)) {
        next.delete(messageId)
      } else {
        next.add(messageId)
      }
      return next
    })
  }

  const toggleData = (messageId: string) => {
    setExpandedData(prev => {
      const next = new Set(prev)
      if (next.has(messageId)) {
        next.delete(messageId)
      } else {
        next.add(messageId)
      }
      return next
    })
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <div key={message.id} className={`message message-${message.role}`}>
          <div className="message-content">
            <div className="message-text" style={{ whiteSpace: 'pre-line' }}>{message.content}</div>
            
            {/* Preview Data button for welcome message */}
            {message.id === 'welcome' && previewData && !previewLoading && (
              <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                <button
                  className="data-preview-toggle"
                  onClick={() => setExpandedPreview(!expandedPreview)}
                  style={{ 
                    padding: '0.5rem 1rem',
                    background: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  {expandedPreview ? 'Hide' : 'Preview'} Data
                </button>
                {expandedPreview && (
                  <div style={{ marginTop: '1rem', textAlign: 'left' }}>
                    <div style={{ marginBottom: '0.5rem' }}>
                      <h3 style={{ margin: '0 0 0.5rem 0', color: '#333', fontSize: '1rem', textAlign: 'left' }}>Sample Data (fhv_with_company view)</h3>
                    </div>
                    <div style={{ overflowX: 'auto', width: '100%' }}>
                      <table style={{ 
                        width: '100%', 
                        borderCollapse: 'collapse', 
                        fontSize: '0.85rem',
                        backgroundColor: 'white'
                      }}>
                        <thead>
                          <tr>
                            {previewData.columns.map((col: string) => (
                              <th key={col} style={{
                                padding: '0.6rem',
                                textAlign: 'left',
                                border: '1px solid #ddd',
                                background: '#f8f9fa',
                                fontWeight: 600,
                                color: '#333'
                              }}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewData.data.map((row: any, idx: number) => (
                            <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? 'white' : '#f9f9f9' }}>
                              {previewData.columns.map((col: string) => (
                                <td key={col} style={{
                                  padding: '0.6rem',
                                  textAlign: 'left',
                                  border: '1px solid #ddd',
                                  color: '#212529'
                                }}>{String(row[col] ?? '')}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <p style={{ 
                      fontSize: '0.85rem', 
                      color: '#666', 
                      marginTop: '1rem',
                      textAlign: 'left'
                    }}>
                      Showing {previewData.row_count} sample rows. Ask questions about this data below.
                    </p>
                  </div>
                )}
              </div>
            )}
            
            {message.sources && message.sources.length > 0 && (
              <div className="message-sources">
                <strong>Sources:</strong> {message.sources.join(', ')}
              </div>
            )}
            
            {message.cached && (
              <span className="cached-badge">Cached</span>
            )}
            
            {message.chart_image_url && (
              <div className="message-chart">
                <img 
                  src={message.chart_image_url} 
                  alt={message.chart?.title || "Chart"} 
                  style={{ maxWidth: '100%', height: 'auto', borderRadius: '8px' }}
                />
              </div>
            )}
            
            {message.chart && !message.chart_image_url && (
              <div className="message-chart">
                <ChartRenderer config={message.chart} data={message.data || []} />
              </div>
            )}
            
            {/* Action buttons container - SQL and Data buttons side by side */}
            {(message.sql || ((message.data_preview && message.data_preview.length > 0) || (message.data && message.data.length > 0))) && (
              <div className="action-buttons-container">
                {message.sql && (
                  <button
                    className="sql-toggle"
                    onClick={() => toggleSQL(message.id)}
                  >
                    {expandedSQL.has(message.id) ? 'Hide' : 'Show'} SQL
                  </button>
                )}
                {((message.data_preview && message.data_preview.length > 0) || (message.data && message.data.length > 0)) && (
                  <button
                    className="data-toggle"
                    onClick={() => toggleData(message.id)}
                  >
                    {expandedData.has(message.id) ? 'Hide' : 'Show'} Data
                  </button>
                )}
              </div>
            )}
            
            {/* SQL section - appears before Data if both are expanded */}
            {message.sql && expandedSQL.has(message.id) && (
              <div className="sql-section">
                <pre className="sql-code">{message.sql}</pre>
              </div>
            )}
            
            {/* Data section - appears after SQL if both are expanded */}
            {((message.data_preview && message.data_preview.length > 0) || (message.data && message.data.length > 0)) && expandedData.has(message.id) && (
              <div className="data-section">
                <div className="message-table">
                  <DataTable 
                    data={message.data_preview || message.data || []} 
                    fullData={message.data}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
      
      {loading && (
        <div className="message message-assistant">
          <div className="message-content">
            <div className="loading-status">
              {loadingStage === 'generating-sql' && (
                <div className="loading-stage">
                  <span className="loading-dot"></span>
                  <span>Generating SQL...</span>
                </div>
              )}
              {loadingStage === 'fetching-data' && (
                <div className="loading-stage">
                  <span className="loading-dot"></span>
                  <span>Fetching data...</span>
                </div>
              )}
              {loadingStage === 'generating-visualization' && (
                <div className="loading-stage">
                  <span className="loading-dot"></span>
                  <span>Generating visualization...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

