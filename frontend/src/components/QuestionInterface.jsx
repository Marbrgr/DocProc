import { useState } from 'react'
import axios from 'axios'

const QuestionInterface = () => {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token')
    return {
      Authorization: `Bearer ${token}`
    }
  }

  const handleAskQuestion = async (e) => {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setError('')

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/documents/question',
        null,
        {
          params: { question: question.trim() },
          headers: getAuthHeaders()
        }
      )

      setAnswer(response.data)
    } catch (error) {
      console.error('Question failed:', error)
      setError(error.response?.data?.detail || 'Question answering failed')
    } finally {
      setLoading(false)
    }
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#27ae60'
    if (confidence >= 0.6) return '#f39c12' 
    if (confidence >= 0.4) return '#e67e22'
    return '#e74c3c'
  }

  return (
    <div className="question-interface">
      <div className="question-header">
        <h3>💬 Ask Questions</h3>
        <p>Get answers based on your document content</p>
      </div>

      <form onSubmit={handleAskQuestion} className="question-form">
        <div className="question-input-group">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="question-input"
            disabled={loading}
            rows={3}
          />
          <button 
            type="submit" 
            className="question-btn"
            disabled={loading || !question.trim()}
          >
            {loading ? (
              <span>
                <span className="question-spinner"></span>
                Thinking...
              </span>
            ) : (
              'Ask Question'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="question-error">
          {error}
        </div>
      )}

      {answer && (
        <div className="answer-section">
          <div className="answer-header">
            <h4>💡 Answer</h4>
            <div className="answer-meta">
              <span 
                className="confidence-badge"
                style={{ backgroundColor: getConfidenceColor(answer.confidence) }}
              >
                {Math.round(answer.confidence * 100)}% confidence
              </span>
              <span className="engine-badge">
                {answer.engine_used}
              </span>
            </div>
          </div>

          <div className="question-asked">
            <strong>Q:</strong> {answer.question}
          </div>

          <div className="answer-content">
            <strong>A:</strong> {answer.answer}
          </div>

          {answer.sources && answer.sources.length > 0 && (
            <div className="answer-sources">
              <h5>📚 Sources</h5>
              <div className="sources-list">
                {answer.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-header">
                      📄 {source.doc_id} • {source.chunk_id}
                    </div>
                    <div className="source-content">
                      {source.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="answer-footer">
            Method: {answer.method}
          </div>
        </div>
      )}
    </div>
  )
}

export default QuestionInterface
