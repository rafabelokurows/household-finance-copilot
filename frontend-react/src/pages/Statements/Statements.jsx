import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { getStatements, uploadDocument } from '../../api/documents'
import Topbar from '../../components/layout/Topbar'
import Spinner from '../../components/shared/Spinner'
import styles from './Statements.module.css'

export default function Statements() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const fileInputRef = useRef(null)

  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [uploadError, setUploadError] = useState(null)

  const { data: statements, isLoading, isError, error } = useQuery({
    queryKey: ['statements'],
    queryFn: () => getStatements(token),
  })

  async function handleFile(file) {
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    setUploadError(null)
    try {
      const result = await uploadDocument(token, file)
      setUploadResult(result)
      queryClient.invalidateQueries({ queryKey: ['statements'] })
    } catch (err) {
      setUploadError(err?.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  function onDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  function onDragLeave(e) {
    e.preventDefault()
    setDragging(false)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  function onFileChange(e) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  function onZoneClick() {
    fileInputRef.current?.click()
  }

  function formatDate(dateStr) {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  return (
    <div className={styles.page}>
      <Topbar title="Statements" />
      <div className={styles.content}>
        <div
          className={`${styles.uploadZone} ${dragging ? styles.dragging : ''}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={onZoneClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onZoneClick()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.webp"
            className={styles.fileInput}
            onChange={onFileChange}
          />
          {uploading ? (
            <Spinner size={20} />
          ) : (
            <>
              <div className={styles.uploadIcon}>📤</div>
              <div className={styles.uploadText}>Drag & drop a bank statement, or click to select</div>
              <div className={styles.uploadHint}>Supports PDF, PNG, JPG, JPEG, WEBP</div>
            </>
          )}
        </div>

        {uploadResult && (
          <div className={styles.uploadResult}>
            ✓ Extracted {uploadResult.tx_count} transaction{uploadResult.tx_count !== 1 ? 's' : ''}
          </div>
        )}
        {uploadError && (
          <div className={styles.uploadError}>{uploadError}</div>
        )}

        <div className={styles.sectionTitle}>Uploaded Statements</div>

        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
            <Spinner size={20} />
          </div>
        ) : isError ? (
          <div className={styles.uploadError}>{error?.message || 'Failed to load statements'}</div>
        ) : !statements?.length ? (
          <div className={styles.empty}>No statements yet</div>
        ) : (
          <div className={styles.statementList}>
            {statements.map((s, i) => (
              <div key={s.id ?? i} className={styles.statementRow}>
                <span className={styles.statementIcon}>📄</span>
                <span className={styles.statementName}>{s.filename || s.name || 'Unnamed'}</span>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                  {s.bank && <span className={styles.statementMeta}>{s.bank}</span>}
                  {(s.period_start || s.period_end) && (
                    <span className={styles.statementMeta}>
                      {formatDate(s.period_start)}{s.period_start && s.period_end ? ' → ' : ''}{formatDate(s.period_end)}
                    </span>
                  )}
                  {s.uploaded_at && (
                    <span className={styles.statementMeta}>{formatDate(s.uploaded_at)}</span>
                  )}
                </div>
                {s.tx_count != null && (
                  <span className={styles.txBadge}>{s.tx_count} tx</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
