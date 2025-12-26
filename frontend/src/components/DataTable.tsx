import { useState } from 'react'
import './DataTable.css'

interface DataTableProps {
  data: any[]
  fullData?: any[]  // Full dataset for CSV download
  maxRows?: number
}

export default function DataTable({ data, fullData, maxRows = 10 }: DataTableProps) {
  const [expanded, setExpanded] = useState(false)
  
  if (!data || data.length === 0) {
    return <div>No data</div>
  }

  const displayData = expanded ? data : data.slice(0, maxRows)
  const hasMore = data.length > maxRows
  const columns = Object.keys(data[0])
  const datasetForCSV = fullData || data

  const downloadCSV = () => {
    if (!datasetForCSV || datasetForCSV.length === 0) return
    
    // Get all columns from the data
    const allColumns = Object.keys(datasetForCSV[0])
    
    // Create CSV header
    const header = allColumns.join(',')
    
    // Create CSV rows
    const rows = datasetForCSV.map(row => 
      allColumns.map(col => {
        const value = row[col]
        // Escape quotes and wrap in quotes if contains comma, newline, or quote
        if (value === null || value === undefined) return ''
        const stringValue = String(value)
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`
        }
        return stringValue
      }).join(',')
    )
    
    // Combine header and rows
    const csvContent = [header, ...rows].join('\n')
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `nyc_taxi_data_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="data-table-container">
      <div className="table-header">
        <div className="table-info">
          Showing {displayData.length} of {data.length} rows
          {fullData && fullData.length > data.length && ` (${fullData.length} total rows available)`}
        </div>
        {datasetForCSV && datasetForCSV.length > 0 && (
          <button className="csv-download-button" onClick={downloadCSV}>
            📥 Download CSV ({datasetForCSV.length} rows)
          </button>
        )}
      </div>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, idx) => (
            <tr key={idx}>
              {columns.map(col => (
                <td key={col}>{String(row[col] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && !expanded && (
        <button className="expand-button" onClick={() => setExpanded(true)}>
          Show all {data.length} rows
        </button>
      )}
    </div>
  )
}

