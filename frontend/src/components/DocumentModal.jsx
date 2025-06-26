import React from 'react'

const DocumentModal = ({ document, isOpen, onClose, onDownload }) => {
  if (!isOpen || !document) return null

  console.log(document)
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 🆕 NEW: Render AI Analysis Section
  const renderAIAnalysis = () => {
    if (!document.ai_document_type || document.ai_document_type === 'unknown') {
      return (
        <div className="ai-analysis">
          <h3>🤖 AI Analysis</h3>
          <div className="analysis-loading">
            <div className="loading-spinner"></div>
            <p className="processing-text">
              {document.extracted_text ? 
                'AI analysis in progress... This may take a few moments.' : 
                'Document processing in progress... This may take a few moments.'
              }
            </p>
          </div>
        </div>
      )
    }

    const confidence = document.ai_confidence ? Math.round(document.ai_confidence * 100) : 0
    
    return (
      <div className="ai-analysis">
        <h3>🤖 AI Analysis</h3>
        <div className="analysis-summary">
          <p><strong>Document Type:</strong> {document.ai_document_type.toUpperCase()}</p>
          <p><strong>Confidence:</strong> {confidence}%</p>
          {document.ai_model_used && (
            <p><strong>Model:</strong> {document.ai_model_used}</p>
          )}
        </div>
        
        {document.ai_key_information && Object.keys(document.ai_key_information).length > 0 && (
          <div className="key-information">
            <h4>📋 Extracted Information</h4>
            <div className="info-grid">
              {Object.entries(document.ai_key_information).map(([key, value]) => {
                // Handle different value types for better display
                let displayValue = value
                if (typeof value === 'boolean') {
                  displayValue = value ? 'Yes' : 'No'
                } else if (value === null || value === undefined || value === '') {
                  displayValue = 'Not found'
                } else {
                  displayValue = String(value)
                }
                
                return (
                  <div key={key} className="info-item">
                    <span className="info-label">{key.replace(/_/g, ' ').toUpperCase()}:</span>
                    <span className="info-value">{displayValue}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{document.file_name}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="document-details">
            <p><strong>File Type:</strong> {document.file_type}</p>
            <p><strong>File Size:</strong> {formatFileSize(document.file_size)}</p>
            <p><strong>Uploaded:</strong> {formatDate(document.created_at)}</p>
          </div>
          
          {/* 🆕 NEW: AI Analysis Section */}
          {renderAIAnalysis()}
          
          {document.extracted_text ? (
            <div className="extracted-text">
              <h3>📄 Extracted Text</h3>
              <div className="text-content">
                {document.extracted_text}
              </div>
            </div>
          ) : (
            <div className="no-text">
              <p>No extracted text available for this document.</p>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button 
            className="btn-secondary" 
            onClick={() => onDownload(document.id, document.file_name)}
          >
            Download
          </button>
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default DocumentModal 