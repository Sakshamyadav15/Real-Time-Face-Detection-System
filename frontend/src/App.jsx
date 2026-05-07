import React, { useEffect } from 'react'
import VideoStream from './components/VideoStream'
import ROITable from './components/ROITable'
import StatusBar from './components/StatusBar'
import useWebSocket from './hooks/useWebSocket'
import useROIData from './hooks/useROIData'
import useWebcamCapture from './hooks/useWebcamCapture'

function App() {
  const { status: wsStatus, frameUrl } = useWebSocket('ws://localhost:8000/ws/stream')
  const { data: roiData, loading: roiLoading } = useROIData('http://localhost:8000/api/roi', 2000)
  const { isCapturing, error: captureError, startCapture, stopCapture } = useWebcamCapture(
    'http://localhost:8000/api/video/ingest',
    15 // 15 FPS
  )

  // Auto-start capture on mount
  useEffect(() => {
    startCapture()
    return () => stopCapture()
  }, [])

  return (
    <>
      {/* Floating glass orbs */}
      <div className="floating-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <div className="app-container">
        <div className="app-header">
          <h1>Face Detection System</h1>
          <p>Real-time AI-powered face detection and tracking</p>
        </div>
        
        {captureError && (
          <div className="error-message">
            <strong>Camera Error:</strong> {captureError}
            <br />
            <small>Please allow camera access and refresh the page.</small>
          </div>
        )}
        
        <StatusBar 
          wsStatus={wsStatus}
          totalDetections={roiData?.total || 0}
        />
        
        <div className="main-grid">
          <VideoStream 
            frameUrl={frameUrl}
            status={wsStatus}
            isCapturing={isCapturing}
          />
          
          <ROITable 
            data={roiData}
            loading={roiLoading}
          />
        </div>
      </div>
    </>
  )
}

export default App
