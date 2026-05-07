import { useState, useEffect, useRef } from 'react'

/**
 * Custom hook for WebSocket connection with exponential backoff reconnect.
 * 
 * @param {string} url - WebSocket URL
 * @returns {Object} - { status, frameUrl }
 */
function useWebSocket(url) {
  const [status, setStatus] = useState('disconnected')
  const [frameUrl, setFrameUrl] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectDelayRef = useRef(1000) // Start with 1 second
  const maxReconnectDelay = 30000 // Max 30 seconds

  useEffect(() => {
    let mounted = true

    const connect = () => {
      if (!mounted) return

      setStatus('connecting')
      
      try {
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          if (!mounted) return
          console.log('WebSocket connected')
          setStatus('live')
          reconnectDelayRef.current = 1000 // Reset delay on successful connection
        }

        ws.onmessage = (event) => {
          if (!mounted) return
          
          // Receive binary JPEG frame
          const blob = event.data
          
          // Create new object URL and revoke previous (functional updater avoids stale closure)
          setFrameUrl((prev) => {
            if (prev) URL.revokeObjectURL(prev)
            return URL.createObjectURL(blob)
          })
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
        }

        ws.onclose = () => {
          if (!mounted) return
          console.log('WebSocket disconnected')
          setStatus('disconnected')
          
          // Attempt reconnect with exponential backoff
          const delay = reconnectDelayRef.current
          console.log(`Reconnecting in ${delay}ms...`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mounted) {
              // Increase delay for next attempt (exponential backoff)
              reconnectDelayRef.current = Math.min(
                reconnectDelayRef.current * 2,
                maxReconnectDelay
              )
              connect()
            }
          }, delay)
        }
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
        setStatus('disconnected')
      }
    }

    connect()

    // Cleanup
    return () => {
      mounted = false
      
      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close()
      }
      
      // Revoke object URL
      if (frameUrl) {
        URL.revokeObjectURL(frameUrl)
      }
    }
  }, [url])

  return { status, frameUrl }
}

export default useWebSocket
