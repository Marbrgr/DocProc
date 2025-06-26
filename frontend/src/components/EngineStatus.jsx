import { useState, useEffect } from 'react'
import axios from 'axios'

const EngineStatus = () => {
  const [engineStatus, setEngineStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [switching, setSwitching] = useState(false)
  const [error, setError] = useState('')

  const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token')
    return {
      Authorization: `Bearer ${token}`
    }
  }

  const fetchEngineStatus = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/v1/documents/engines/status',
        { headers: getAuthHeaders() }
      )
      setEngineStatus(response.data)
      setError('')
    } catch (error) {
      console.error('Failed to fetch engine status:', error)
      setError('Failed to load engine status')
    } finally {
      setLoading(false)
    }
  }

  const switchEngine = async (engineType) => {
    setSwitching(true)
    try {
      await axios.post(
        'http://localhost:8000/api/v1/documents/engines/switch',
        null,
        {
          params: { engine_type: engineType },
          headers: getAuthHeaders()
        }
      )
      
      // Refresh status after switching
      await fetchEngineStatus()
      setError('')
    } catch (error) {
      console.error('Failed to switch engine:', error)
      setError(error.response?.data?.detail || 'Failed to switch engine')
    } finally {
      setSwitching(false)
    }
  }

  useEffect(() => {
    fetchEngineStatus()
  }, [])

  if (loading) {
    return (
      <div className="engine-status loading">
        Loading engine status...
      </div>
    )
  }

  if (error) {
    return (
      <div className="engine-status error">
        {error}
        <button onClick={fetchEngineStatus} className="retry-btn">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="engine-status">
      <div className="status-header">
        <h3>🚀 AI Engine Status</h3>
        <button onClick={fetchEngineStatus} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      <div className="current-engine">
        <h4>Current Engine: {engineStatus?.current_engine || 'None'}</h4>
      </div>

      <div className="available-engines">
        <h5>Available Engines:</h5>
        <div className="engines-grid">
          {engineStatus?.available_engines?.map((engineType) => {
            const engineInfo = engineStatus.engine_details[engineType]
            const isCurrent = engineType === engineStatus.current_engine
            
            return (
              <div 
                key={engineType} 
                className={`engine-card ${isCurrent ? 'current' : ''}`}
              >
                <div className="engine-header">
                  <h6>{engineType.toUpperCase()}</h6>
                  {isCurrent && <span className="current-badge">ACTIVE</span>}
                </div>
                
                <div className="engine-info">
                  <div className="info-row">
                    <span>Status:</span>
                    <span className={`status ${engineInfo.is_available ? 'available' : 'unavailable'}`}>
                      {engineInfo.is_available ? '✅ Available' : '❌ Unavailable'}
                    </span>
                  </div>
                  
                  {engineInfo.model && (
                    <div className="info-row">
                      <span>Model:</span>
                      <span>{engineInfo.model}</span>
                    </div>
                  )}
                  
                  {engineInfo.rag_implementation && (
                    <div className="info-row">
                      <span>RAG:</span>
                      <span>{engineInfo.rag_implementation}</span>
                    </div>
                  )}
                  
                  {engineInfo.documents_stored !== undefined && (
                    <div className="info-row">
                      <span>Documents:</span>
                      <span>{engineInfo.documents_stored}</span>
                    </div>
                  )}
                </div>

                <div className="engine-features">
                  <h6>Features:</h6>
                  <ul className="features-list">
                    {Object.entries(engineInfo.features || {}).map(([feature, available]) => (
                      <li key={feature} className={available ? 'available' : 'unavailable'}>
                        {available ? '✅' : '❌'} {feature.replace(/_/g, ' ')}
                      </li>
                    ))}
                  </ul>
                </div>

                {!isCurrent && engineInfo.is_available && (
                  <button 
                    onClick={() => switchEngine(engineType)}
                    disabled={switching}
                    className="switch-btn"
                  >
                    {switching ? 'Switching...' : 'Switch to this engine'}
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default EngineStatus
