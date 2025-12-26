import { useEffect, useState } from 'react'
import './DataPreview.css'

interface PreviewData {
  columns: string[]
  data: any[]
  row_count: number
  error?: string
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// Use the same API path helper pattern as chat.ts
const getApiPath = (endpoint: string) => {
  if (API_URL.startsWith('/')) {
    // Using Vite proxy, endpoint already includes /api
    return `${API_URL}${endpoint}`
  } else {
    // Direct connection, need to add /api
    return `${API_URL}/api${endpoint}`
  }
}

export default function DataPreview() {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const response = await fetch(getApiPath('/data-preview'))
        if (!response.ok) {
          throw new Error('Failed to fetch data preview')
        }
        const data = await response.json()
        setPreviewData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data preview')
      } finally {
        setLoading(false)
      }
    }

    fetchPreview()
  }, [])

  if (loading) {
    return (
      <div className="data-preview-container">
        <button
          className="data-preview-toggle"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Hide' : 'Preview'} Data
        </button>
        {expanded && (
          <div className="data-preview-loading">Loading data preview...</div>
        )}
      </div>
    )
  }

  if (error || previewData?.error) {
    return null // Don't show error, just don't display preview
  }

  if (!previewData || !previewData.data || previewData.data.length === 0) {
    return null
  }

  return (
    <div className="data-preview-container">
      <button
        className="data-preview-toggle"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? 'Hide' : 'Preview'} Data
      </button>
      {expanded && (
        <>
          <div className="data-preview-header">
            <h3>Sample Data (fhv_with_company view)</h3>
          </div>
          <div className="data-preview-table-wrapper">
            <table className="data-preview-table">
              <thead>
                <tr>
                  {previewData.columns.map(col => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.data.map((row, idx) => (
                  <tr key={idx}>
                    {previewData.columns.map(col => (
                      <td key={col}>{String(row[col] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="data-preview-note">
            Showing {previewData.row_count} sample rows. Ask questions about this data below.
          </p>
        </>
      )}
    </div>
  )
}

