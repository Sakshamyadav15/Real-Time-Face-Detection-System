import { useState, useEffect, useRef } from 'react'

/**
 * Custom hook for polling ROI data from the API.
 * 
 * @param {string} url - API endpoint URL
 * @param {number} interval - Polling interval in milliseconds
 * @returns {Object} - { data, loading, error }
 */
function useROIData(url, interval = 2000) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    let mounted = true

    const fetchData = async () => {
      try {
        console.log('Fetching ROI data from:', `${url}?limit=50&offset=0`)
        const response = await fetch(`${url}?limit=50&offset=0`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const json = await response.json()
        console.log('ROI data received:', json)
        
        if (mounted) {
          setData(json)
          setLoading(false)
          setError(null)
        }
      } catch (err) {
        console.error('Failed to fetch ROI data:', err)
        if (mounted) {
          setError(err.message)
          setLoading(false)
        }
      }
    }

    // Initial fetch
    fetchData()

    // Set up polling
    intervalRef.current = setInterval(fetchData, interval)

    // Cleanup
    return () => {
      mounted = false
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [url, interval])

  return { data, loading, error }
}

export default useROIData
