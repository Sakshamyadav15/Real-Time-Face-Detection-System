import React from 'react'

/**
 * VideoStream component displays the live annotated video feed.
 * 
 * @param {Object} props
 * @param {string} props.frameUrl - Object URL of the current frame
 * @param {string} props.status - Connection status (connecting, live, disconnected)
 * @param {boolean} props.isCapturing - Whether webcam is capturing
 */
function VideoStream({ frameUrl, status, isCapturing }) {
  const getStatusClass = () => {
    switch (status) {
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
    switch (status) {
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
    <div className="glass-card">
      <div className="card-header">
        <h2>Live Video Stream</h2>
        <span className={`card-badge ${getStatusClass()}`}>
          {getStatusText()}
        </span>
      </div>
      
      <div className="video-container">
        {frameUrl ? (
          <img 
            src={frameUrl} 
            alt="Live video stream with face detection"
          />
        ) : (
          <div className="video-placeholder">
            <p style={{ fontSize: '1.1rem', fontWeight: '500' }}>
              {status === 'connecting' && 'Connecting to server...'}
              {status === 'disconnected' && 'Disconnected'}
              {status === 'live' && !isCapturing && 'Waiting for camera...'}
              {status === 'live' && isCapturing && 'Processing frames...'}
            </p>
            <p style={{ fontSize: '0.9rem', opacity: 0.7 }}>
              {status === 'live' && isCapturing && 'Face detection active'}
              {status === 'disconnected' && 'Attempting to reconnect...'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default VideoStream
