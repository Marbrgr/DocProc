import { useState, useEffect } from 'react'
import axios from 'axios'
import DocumentCard from './DocumentCard'
import DocumentModal from './DocumentModal'
import UploadButton from './UploadButton'

const Dashboard = () => {
    const [user, setUser] = useState(null)
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [selectedDocument, setSelectedDocument] = useState(null)
    const [isModalOpen, setIsModalOpen] = useState(false)

    useEffect(() => {
        fetchUserAndDocuments()
    }, [])

    const fetchUserAndDocuments = async () => {
        try {
            const token = localStorage.getItem('jwt_token')
            if (!token) {
                setError('No authentication token found')
                setLoading(false)
                return
            }

            const headers = {
                Authorization: `Bearer ${token}`
            }

            const [userResponse, documentsResponse] = await Promise.all([
                axios.get('http://localhost:8000/api/v1/auth/me', { headers }),
                axios.get('http://localhost:8000/api/v1/documents/list', { headers })
            ])

            setUser(userResponse.data)
            setDocuments(documentsResponse.data)
            setError('')
        } catch (error) {
            console.error('Failed to fetch user and documents:', error)
            setError('Failed to load dashboard data')

            if (error.response?.status === 401) {
                localStorage.removeItem('jwt_token')
                window.location.reload()
            }
        } finally {
            setLoading(false)
        }
    }

    const getAuthHeaders = () => {
        const token = localStorage.getItem('jwt_token')
        return {
            Authorization: `Bearer ${token}`
        }
    }

    const handleUploadSuccess = (uploadedDocument) => {
        // Refresh the document list after successful upload
        fetchUserAndDocuments()
    }

    const handleView = async (documentId) => {
        try {
            const response = await axios.get(
                `http://localhost:8000/api/v1/documents/${documentId}`,
                { headers: getAuthHeaders() }
            )
            setSelectedDocument(response.data)
            setIsModalOpen(true)
        } catch (error) {
            console.error('Failed to fetch document details:', error)
            alert('Failed to load document details')
        }
    }

    const handleDownload = async (documentId, fileName) => {
        try {
            const response = await axios.get(
                `http://localhost:8000/api/v1/documents/${documentId}/download`,
                {
                    headers: getAuthHeaders(),
                    responseType: 'blob'
                }
            )

            // Create download link
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', fileName)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
        } catch (error) {
            console.error('Failed to download document:', error)
            alert('Failed to download document')
        }
    }

    const handleDelete = async (documentId, fileName) => {
        if (!confirm(`Are you sure you want to delete "${fileName}"? This action cannot be undone.`)) {
            return
        }

        try {
            await axios.delete(
                `http://localhost:8000/api/v1/documents/${documentId}`,
                { headers: getAuthHeaders() }
            )

            // Remove document from local state
            setDocuments(documents.filter(doc => doc.id !== documentId))
            alert('Document deleted successfully')
        } catch (error) {
            console.error('Failed to delete document:', error)
            alert('Failed to delete document')
        }
    }

    const closeModal = () => {
        setIsModalOpen(false)
        setSelectedDocument(null)
    }

    const handleLogout = () => {
        localStorage.removeItem('jwt_token')
        window.location.reload()
    }

    if (loading) {
        return (
            <div className="dashboard">
                <div className="loading">Loading dashboard...</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="dashboard">
                <div className="error">Error: {error}</div>
            </div>
        )
    }

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <div className="user-info">
                    <h1>Welcome back, {user?.username}!</h1>
                    <p className="user-details">
                        {user?.email} • {user?.documents_processed} documents processed
                    </p>
                </div>
                <button onClick={handleLogout} className="logout-btn">
                    Logout
                </button>
            </div>

            <div className="documents-section">
                <div className="section-header">
                    <h2>Your Documents</h2>
                    <div className="document-count">
                        {documents.length} document{documents.length !== 1 ? 's' : ''}
                    </div>
                </div>

                <UploadButton onUploadSuccess={handleUploadSuccess} />

                {documents.length === 0 ? (
                    <div className="empty-state">
                        <p>No documents uploaded yet.</p>
                        <p>Upload your first document to get started!</p>
                    </div>
                ) : (
                    <div className="documents-list">
                        {documents.map((doc) => (
                            <DocumentCard
                                key={doc.id}
                                document={doc}
                                onView={handleView}
                                onDownload={handleDownload}
                                onDelete={handleDelete}
                            />
                        ))}
                    </div>
                )}
            </div>

            <DocumentModal
                document={selectedDocument}
                isOpen={isModalOpen}
                onClose={closeModal}
                onDownload={handleDownload}
            />
        </div>
    )
}

export default Dashboard