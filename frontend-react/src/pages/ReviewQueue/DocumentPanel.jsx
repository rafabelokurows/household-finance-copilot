import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { getDocument } from '../../api/transactions'
import Spinner from '../../components/shared/Spinner'
import ErrorBanner from '../../components/shared/ErrorBanner'
import styles from './DocumentPanel.module.css'

function base64ToBlob(base64, contentType) {
  const byteChars = atob(base64)
  const byteArray = new Uint8Array(byteChars.length)
  for (let i = 0; i < byteChars.length; i++) {
    byteArray[i] = byteChars.charCodeAt(i)
  }
  return new Blob([byteArray], { type: contentType })
}

function formatUploadDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', year: 'numeric' })
}

function DocumentViewer({ doc }) {
  const docData = doc?.data
  const contentType = doc?.content_type

  const blobUrl = useMemo(() => {
    if (!docData) return null
    const blob = base64ToBlob(docData, contentType)
    return URL.createObjectURL(blob)
  }, [docData, contentType])

  function handleDownload() {
    if (!blobUrl) return
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = doc.filename ?? 'document'
    a.click()
  }

  const isImage = contentType?.startsWith('image/')

  return (
    <>
      <div className={styles.header}>
        <span className={styles.filename}>{doc.filename}</span>
        <span className={styles.uploadDate}>{formatUploadDate(doc.upload_date)}</span>
        <button className={styles.downloadBtn} onClick={handleDownload}>
          Download
        </button>
      </div>
      <div className={styles.viewer}>
        {blobUrl && (
          isImage
            ? <img src={blobUrl} alt={doc.filename} />
            : <iframe src={blobUrl} title={doc.filename} />
        )}
      </div>
    </>
  )
}

export default function DocumentPanel({ txId }) {
  const { token } = useAuth()

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['document', txId],
    queryFn: () => getDocument(token, txId),
    enabled: !!txId,
  })

  if (!txId) {
    return (
      <div className={styles.panel}>
        <div className={styles.placeholder}>Select 📄 to view document</div>
      </div>
    )
  }

  return (
    <div className={styles.panel}>
      {isLoading && (
        <div className={styles.center}><Spinner size={20} /></div>
      )}
      {isError && (
        <ErrorBanner message={error?.message ?? 'Failed to load document'} onRetry={refetch} />
      )}
      {!isLoading && !isError && data && (
        <DocumentViewer doc={data} />
      )}
    </div>
  )
}
