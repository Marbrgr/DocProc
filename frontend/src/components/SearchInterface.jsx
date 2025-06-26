import { useState } from 'react'
import axios from 'axios'

const SearchInterface = () => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token')
    return {
      Authorization: `Bearer ${token}`
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError('')

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/documents/search',
        null,
        {
          params: { query: query.trim() },
          headers: getAuthHeaders()
        }
      )

      setResults(response.data)
    } catch (error) {
      console.error('Search failed:', error)
      setError(error.response?.data?.detail || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-interface">
      <div className="search-header">
        <h3>🔍 Search Documents</h3>
        <p>Find relevant information across all your documents</p>
      </div>

      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your documents..."
            className="search-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="search-btn"
            disabled={loading || !query.trim()}
          >
            {loading ? (
              <span className="search-spinner"></span>
            ) : (
              'Search'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="search-error">
          {error}
        </div>
      )}

      {results && (
        <div className="search-results">
          <div className="results-header">
            <h4>Search Results</h4>
            <span className="results-count">
              {results.total_results} result{results.total_results !== 1 ? 's' : ''} 
              • Engine: {results.engine_used}
            </span>
          </div>

          {results.results.length === 0 ? (
            <div className="no-results">
              <p>No relevant documents found for "{results.query}"</p>
              <p>Try using different keywords or check if you have documents uploaded.</p>
            </div>
          ) : (
            <div className="results-list">
              {results.results.map((result, index) => (
                <div key={index} className="search-result-item">
                  <div className="result-header">
                    <span className="result-doc-id">📄 {result.doc_id}</span>
                    {result.similarity && (
                      <span className="similarity-score">
                        {Math.round(result.similarity * 100)}% match
                      </span>
                    )}
                  </div>
                  <div className="result-content">
                    {result.content}
                  </div>
                  <div className="result-meta">
                    Chunk: {result.chunk_id} • Engine: {result.engine}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SearchInterface
