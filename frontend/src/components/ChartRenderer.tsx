import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import './ChartRenderer.css'

interface ChartRendererProps {
  config: {
    type: 'line' | 'bar'
    x: string
    y: string
    series?: string
    title?: string
  }
  data: any[]
}

export default function ChartRenderer({ config, data }: ChartRendererProps) {
  if (!data || data.length === 0) {
    return <div>No data to display</div>
  }

  // Transform data for Recharts
  // If series is specified, group by x-axis value and create separate series columns
  let chartData: any[]
  let seriesValues: string[] = []
  
  if (config.series) {
    // Get all unique series values
    seriesValues = Array.from(new Set(data.map(d => String(d[config.series!]))))
    
    // Group by x-axis value
    const grouped: Record<string, Record<string, any>> = {}
    
    data.forEach(row => {
      const xValue = String(row[config.x])
      const seriesValue = String(row[config.series!])
      const yValue = row[config.y]
      
      if (!grouped[xValue]) {
        grouped[xValue] = { [config.x]: xValue }
        // Initialize all series to 0
        seriesValues.forEach(s => {
          grouped[xValue][s] = 0
        })
      }
      
      grouped[xValue][seriesValue] = yValue
    })
    
    // Sort by x value (convert to number if possible)
    chartData = Object.values(grouped).sort((a, b) => {
      const aVal = Number(a[config.x]) || 0
      const bVal = Number(b[config.x]) || 0
      return aVal - bVal
    })
  } else {
    chartData = data.map(row => ({
      [config.x]: row[config.x],
      [config.y]: row[config.y]
    })).sort((a, b) => {
      const aVal = Number(a[config.x]) || 0
      const bVal = Number(b[config.x]) || 0
      return aVal - bVal
    })
  }
  
  // Generate consistent colors for series
  const colors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1',
    '#d084d0', '#ffb347', '#87ceeb', '#da70d6', '#98d8c8'
  ]

  if (config.type === 'line') {
    return (
      <div className="chart-container">
        {config.title && <h4 className="chart-title">{config.title}</h4>}
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.x} />
            <YAxis />
            <Tooltip />
            {config.series ? (
              <>
                <Legend />
                {seriesValues.map((series, idx) => (
                  <Line
                    key={series}
                    type="monotone"
                    dataKey={series}
                    stroke={colors[idx % colors.length]}
                    fill={colors[idx % colors.length]}
                  />
                ))}
              </>
            ) : (
              <Line type="monotone" dataKey={config.y} stroke="#8884d8" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  } else {
    return (
      <div className="chart-container">
        {config.title && <h4 className="chart-title">{config.title}</h4>}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.x} />
            <YAxis />
            <Tooltip />
            {config.series ? (
              <>
                <Legend />
                {seriesValues.map((series, idx) => (
                  <Bar
                    key={series}
                    dataKey={series}
                    fill={colors[idx % colors.length]}
                  />
                ))}
              </>
            ) : (
              <Bar dataKey={config.y} fill="#8884d8" />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }
}

