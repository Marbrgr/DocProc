import { useState, useRef } from 'react'
import axios from 'axios'

const UploadButton = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef(null)

  const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token')
    return {
      Authorization: `Bearer ${token}`
    }
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      uploadFile(file)
    }
  }

  const uploadFile = async (file) => {
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      alert('File size exceeds 10MB limit')
      return
    }

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      alert('Only PDF, PNG, and JPEG files are supported')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/documents/upload',
        formData,
        {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
            setUploadProgress(progress)
          }
        }
      )

      // Success feedback
      alert(`File "${file.name}" uploaded successfully!`)
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
      // Notify parent component to refresh document list
      if (onUploadSuccess) {
        onUploadSuccess(response.data)
      }

    } catch (error) {
      console.error('Upload failed:', error)
      if (error.response?.status === 401) {
        alert('Authentication failed. Please log in again.')
        localStorage.removeItem('jwt_token')
        window.location.reload()
      } else {
        alert(`Upload failed: ${error.response?.data?.detail || error.message}`)
      }
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const triggerFileSelect = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="upload-button-container">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".pdf,.png,.jpg,.jpeg"
        style={{ display: 'none' }}
      />
      
      <button 
        onClick={triggerFileSelect}
        disabled={uploading}
        className="upload-btn"
      >
        {uploading ? (
          <span>
            <span className="upload-spinner"></span>
            Uploading... {uploadProgress}%
          </span>
        ) : (
          <span>
            <span className="upload-icon">📁</span>
            Upload Document
          </span>
        )}
      </button>

      {uploading && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <div className="progress-text">{uploadProgress}%</div>
        </div>
      )}
    </div>
  )
}

export default UploadButton 