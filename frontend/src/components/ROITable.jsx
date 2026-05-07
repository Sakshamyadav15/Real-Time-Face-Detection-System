import React from 'react'

/**
 * ROITable component displays the history of ROI detections.
 * 
 * @param {Object} props
 * @param {Object} props.data - ROI data from API
 * @param {boolean} props.loading - Loading state
 */
function ROITable({ data, loading }) {
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  const formatConfidence = (confidence, hasFace) => {
    if (!hasFace) {
      return 'No face'
    }
    if (confidence === null || confidence === undefined) {
      return 'N/A'
    }
    return `${(confidence * 100).toFixed(1)}%`
  }

  if (loading) {
    return (
      <div className="glass-card">
        <div className="card-header">
          <h2>Detection History</h2>
        </div>
        <div className="empty-state">
          <p>Loading detection history...</p>
        </div>
      </div>
    )
  }

  if (!data || !data.items || data.items.length === 0) {
    return (
      <div className="glass-card">
        <div className="card-header">
          <h2>Detection History</h2>
        </div>
        <div className="empty-state">
          <p>No detections yet</p>
          <p style={{ fontSize: '0.9rem', marginTop: '10px', opacity: 0.7 }}>
            Start capturing frames to see detection history
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card">
      <div className="card-header">
        <h2>Detection History</h2>
        <span className="card-badge">{data.total} total</span>
      </div>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>X</th>
              <th>Y</th>
              <th>Size</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.id}>
                <td>{formatTimestamp(item.captured_at)}</td>
                <td>{item.x}</td>
                <td>{item.y}</td>
                <td>{item.width}×{item.height}</td>
                <td>{formatConfidence(item.confidence, item.has_face)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ROITable
