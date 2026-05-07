import React from 'react'

/**
 * StatusBar component displays connection status and detection count.
 * 
 * @param {Object} props
 * @param {string} props.wsStatus - WebSocket connection status
 * @param {number} props.totalDetections - Total number of detections
 */
function StatusBar({ wsStatus, totalDetections }) {
  const getStatusClass = () => {
    switch (wsStatus) {
      case 'connecting':
        return 'status-connecting'
      case 'live':
        return 'status-live'
      case 'disconnected':
        return 'status-disconnected'
      default:
        return 'status-disconnected'
    }
  }

  const getStatusText = () => {
    switch (wsStatus) {
      case 'connecting':
        return 'Connecting'
      case 'live':
        return 'Live'
      case 'disconnected':
        return 'Disconnected'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="status-bar">
      <div className={`status-badge ${getStatusClass()}`}>
        <span className="status-dot"></span>
        <span>Connection: {getStatusText()}</span>
      </div>
      <div className="status-badge">
        <span>Total Detections: {totalDetections}</span>
      </div>
    </div>
  )
}

export default StatusBar
