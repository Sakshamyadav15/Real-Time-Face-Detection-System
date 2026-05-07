import { useState, useEffect, useRef } from 'react'

/**
 * Custom hook for webcam capture and frame ingestion.
 * 
 * @param {string} ingestUrl - Backend ingest endpoint URL
 * @param {number} fps - Target frames per second (default: 15)
 * @returns {Object} - { isCapturing, error, startCapture, stopCapture }
 */
function useWebcamCapture(ingestUrl, fps = 15) {
  const [isCapturing, setIsCapturing] = useState(false)
  const [error, setError] = useState(null)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const intervalRef = useRef(null)
  const sessionIdRef = useRef(null)
  const frameSeqRef = useRef(0)

  const captureAndSendFrame = async () => {
    if (!videoRef.current || !canvasRef.current) return

    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    // Set canvas size to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert canvas to blob (JPEG)
    canvas.toBlob(async (blob) => {
      if (!blob) return

      try {
        // Create form data
        const formData = new FormData()
        formData.append('frame', blob, 'frame.jpg')

        // Send to backend
        const response = await fetch(ingestUrl, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          console.error('Failed to ingest frame:', response.statusText)
        }

        frameSeqRef.current++
      } catch (err) {
        console.error('Error sending frame:', err)
      }
    }, 'image/jpeg', 0.8)
  }

  const startCapture = async () => {
    try {
      setError(null)

      // Request webcam access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        }
      })

      streamRef.current = stream

      // Create video element if not exists
      if (!videoRef.current) {
        videoRef.current = document.createElement('video')
        videoRef.current.autoplay = true
        videoRef.current.playsInline = true
      }

      // Create canvas element if not exists
      if (!canvasRef.current) {
        canvasRef.current = document.createElement('canvas')
      }

      // Set video source
      videoRef.current.srcObject = stream

      // Wait for video to be ready
      await new Promise((resolve) => {
        videoRef.current.onloadedmetadata = resolve
      })

      // Generate session ID
      sessionIdRef.current = crypto.randomUUID()
      frameSeqRef.current = 0

      // Start capturing frames at specified FPS
      const interval = 1000 / fps
      intervalRef.current = setInterval(captureAndSendFrame, interval)

      setIsCapturing(true)
      console.log(`Started webcam capture at ${fps} FPS`)
    } catch (err) {
      console.error('Failed to start webcam:', err)
      setError(err.message)
      setIsCapturing(false)
    }
  }

  const stopCapture = () => {
    // Stop interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    // Stop video stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    // Clear video source
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }

    setIsCapturing(false)
    console.log('Stopped webcam capture')
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCapture()
    }
  }, [])

  return {
    isCapturing,
    error,
    startCapture,
    stopCapture
  }
}

export default useWebcamCapture
