import { useState, useEffect } from 'react'
import axios from 'axios'
import DocumentCard from './DocumentCard'
import DocumentModal from './DocumentModal'
import UploadButton from './UploadButton'
import SearchInterface from './SearchInterface'
import QuestionInterface from './QuestionInterface'
import EngineStatus from './EngineStatus'

const Dashboard = () => {
    const [user, setUser] = useState(null)
    const [documents, setDocuments] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [selectedDocument, setSelectedDocument] = useState(null)
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [activeTab, setActiveTab] = useState('documents')

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

            // 🆕 NEW: Check if document is still processing and poll for updates
            if (!response.data.ai_document_type || response.data.ai_document_type === 'unknown') {
                console.log('🔄 Document may still be processing, starting polling...')
                pollForDocumentUpdates(documentId)
            }
        } catch (error) {
            console.error('Failed to fetch document details:', error)
            alert('Failed to load document details')
        }
    }

    // 🆕 NEW: Poll for document processing updates
    const pollForDocumentUpdates = async (documentId, maxAttempts = 10) => {
        let attempts = 0
        
        const poll = async () => {
            attempts++
            console.log(`🔄 Polling attempt ${attempts}/${maxAttempts} for document ${documentId}`)
            
            try {
                const response = await axios.get(
                    `http://localhost:8000/api/v1/documents/${documentId}`,
                    { headers: getAuthHeaders() }
                )
                
                const hasAIAnalysis = response.data.ai_document_type && 
                                    response.data.ai_document_type !== 'unknown' &&
                                    response.data.extracted_text

                if (hasAIAnalysis) {
                    console.log('✅ AI analysis completed, updating document view')
                    setSelectedDocument(response.data)
                    // Also refresh the documents list to show updated info
                    fetchUserAndDocuments()
                    return
                }

                if (attempts < maxAttempts) {
                    // Continue polling every 2 seconds
                    setTimeout(poll, 2000)
                } else {
                    console.log('⏰ Polling timeout reached')
                }
                
            } catch (error) {
                console.error('Polling error:', error)
            }
        }

        // Start polling after 3 seconds to give processing time
        setTimeout(poll, 3000)
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
            const response = await axios.delete(
                `http://localhost:8000/api/v1/documents/${documentId}`,
                { headers: getAuthHeaders() }
            )

            setDocuments(documents.filter(doc => doc.id !== documentId))
            
            // Show detailed deletion result
            const vectorCleanup = response.data.vector_cleanup || []
            const cleanupSummary = vectorCleanup.map(r => `${r.engine}: ${r.removed ? '✅' : '❌'}`).join(', ')
            alert(`Document deleted successfully\nVector cleanup: ${cleanupSummary}`)
        } catch (error) {
            console.error('Failed to delete document:', error)
            alert('Failed to delete document')
        }
    }

    const handleVectorCleanup = async () => {
        if (!confirm('This will clean up orphaned search entries for deleted documents. Continue?')) {
            return
        }

        try {
            const response = await axios.post(
                'http://localhost:8000/api/v1/documents/cleanup-vectors',
                {},
                { headers: getAuthHeaders() }
            )

            const results = response.data.cleanup_results || []
            const summary = results.map(r => 
                `${r.engine}: ${r.orphaned_found || 0} found, ${r.orphaned_removed || 0} removed`
            ).join('\n')
            
            alert(`Vector cleanup completed!\n\n${summary}`)
        } catch (error) {
            console.error('Failed to cleanup vectors:', error)
            alert('Failed to cleanup vectors')
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

            <div className="tab-navigation">
                <button 
                    className={`tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
                    onClick={() => setActiveTab('documents')}
                >
                    📁 Documents
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
                    onClick={() => setActiveTab('search')}
                >
                    🔍 Search
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'qa' ? 'active' : ''}`}
                    onClick={() => setActiveTab('qa')}
                >
                    💬 Q&A
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'engines' ? 'active' : ''}`}
                    onClick={() => setActiveTab('engines')}
                >
                    🚀 Engines
                </button>
            </div>

            <div className="tab-content">
                {activeTab === 'documents' && (
                    <div className="documents-section">
                        <div className="section-header">
                            <h2>Your Documents</h2>
                            <div className="section-actions">
                                <div className="document-count">
                                    {documents.length} document{documents.length !== 1 ? 's' : ''}
                                </div>
                                <button 
                                    onClick={handleVectorCleanup}
                                    className="cleanup-btn"
                                    title="Clean up orphaned search entries"
                                >
                                    🧹 Cleanup Search
                                </button>
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
                )}

                {activeTab === 'search' && <SearchInterface />}
                {activeTab === 'qa' && <QuestionInterface />}
                {activeTab === 'engines' && <EngineStatus />}
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