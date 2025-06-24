import React from 'react'

const DocumentCard = ({ document, onView, onDownload, onDelete }) => {
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

  // 🆕 NEW: Format AI document type for display
  const getDocumentTypeDisplay = () => {
    if (!document.ai_document_type || document.ai_document_type === 'unknown') {
      return null
    }
    
    const typeColors = {
      'invoice': '#e74c3c',
      'contract': '#3498db', 
      'receipt': '#27ae60',
      'form': '#f39c12',
      'letter': '#9b59b6',
      'report': '#34495e',
      'other': '#95a5a6'
    }

    const color = typeColors[document.ai_document_type] || '#95a5a6'
    const confidence = document.ai_confidence ? Math.round(document.ai_confidence * 100) : 0

    return (
      <span 
        className="ai-type-badge" 
        style={{ backgroundColor: color }}
        title={`AI Classification: ${confidence}% confidence`}
      >
        {document.ai_document_type.toUpperCase()}
      </span>
    )
  }

  return (
    <div className="document-card">
      <div className="document-info">
        <div className="document-title-row">
          <h3 className="document-name">{document.file_name}</h3>
          {getDocumentTypeDisplay()}
        </div>
        <div className="document-meta">
          <span className="file-type">{document.file_type}</span>
          <span className="file-size">{formatFileSize(document.file_size)}</span>
          <span className="upload-date">{formatDate(document.created_at)}</span>
        </div>
      </div>
      <div className="document-actions">
        <button 
          className="btn-secondary" 
          onClick={() => onView(document.id)}
        >
          View
        </button>
        <button 
          className="btn-secondary" 
          onClick={() => onDownload(document.id, document.file_name)}
        >
          Download
        </button>
        <button 
          className="btn-danger" 
          onClick={() => onDelete(document.id, document.file_name)}
        >
          Delete
        </button>
      </div>
    </div>
  )
}

export default DocumentCard
