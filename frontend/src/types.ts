export interface ChatResponse {
  answer: string
  sql?: string
  data?: any[]  // Full dataset for CSV download
  data_preview?: any[]  // Preview for table display
  chart?: {
    type: 'line' | 'bar' | 'scatter' | 'hist' | 'box' | 'heatmap' | 'none'
    title?: string
    x: {
      col: string
      dtype?: 'datetime' | 'category' | 'number'
      sort?: boolean
    } | string
    y: {
      col: string
      dtype?: 'number'
      sort?: boolean
    } | string
    series?: string | null
    top_k?: {
      col?: string | null
      k?: number
      by?: string
      order?: 'asc' | 'desc'
    }
    orientation?: 'vertical' | 'horizontal'
    stacked?: boolean
    limits?: {
      max_points?: number
    }
  }
  chart_image_url?: string
  sources?: string[]
  mode: 'rag' | 'template' | 'sql' | 'error'
  cached?: boolean
}

