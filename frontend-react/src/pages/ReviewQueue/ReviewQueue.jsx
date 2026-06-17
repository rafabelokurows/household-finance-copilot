import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { getPending, pollEmail } from '../../api/transactions'
import Topbar from '../../components/layout/Topbar'
import ReviewCard from './ReviewCard'
import DocumentPanel from './DocumentPanel'
import Spinner from '../../components/shared/Spinner'
import ErrorBanner from '../../components/shared/ErrorBanner'
import styles from './ReviewQueue.module.css'

const SORT_OPTIONS = [
  { value: 'date-desc', label: 'Date: Newest' },
  { value: 'date-asc', label: 'Date: Oldest' },
  { value: 'amount-high', label: 'Amount: High → Low' },
  { value: 'amount-low', label: 'Amount: Low → High' },
  { value: 'confidence-high', label: 'Confidence: High → Low' },
  { value: 'confidence-low', label: 'Confidence: Low → High' },
]

function sortTransactions(txs, sort) {
  if (!txs) return []
  const arr = [...txs]
  switch (sort) {
    case 'date-desc':
      return arr.sort((a, b) => new Date(b.date) - new Date(a.date))
    case 'date-asc':
      return arr.sort((a, b) => new Date(a.date) - new Date(b.date))
    case 'amount-high':
      return arr.sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
    case 'amount-low':
      return arr.sort((a, b) => Math.abs(a.amount) - Math.abs(b.amount))
    case 'confidence-high':
      return arr.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
    case 'confidence-low':
      return arr.sort((a, b) => (a.confidence ?? 0) - (b.confidence ?? 0))
    default:
      return arr
  }
}

export default function ReviewQueue() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [sort, setSort] = useState('date-desc')
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [pollLoading, setPollLoading] = useState(false)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['pending'],
    queryFn: () => getPending(token),
  })

  async function handlePollGmail() {
    setPollLoading(true)
    try {
      await pollEmail(token)
      queryClient.invalidateQueries({ queryKey: ['pending'] })
    } finally {
      setPollLoading(false)
    }
  }

  const txList = data?.transactions ?? (Array.isArray(data) ? data : [])
  const sorted = sortTransactions(txList, sort)

  return (
    <div className={styles.page}>
      <Topbar title="Review Queue">
        <select
          className={styles.sortSelect}
          value={sort}
          onChange={(e) => setSort(e.target.value)}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button
          className={styles.pollBtn}
          onClick={handlePollGmail}
          disabled={pollLoading}
        >
          {pollLoading ? 'Polling…' : 'Poll Gmail'}
        </button>
      </Topbar>

      <div className={styles.body}>
        <div className={styles.list}>
          {isLoading && (
            <div className={styles.center}><Spinner size={20} /></div>
          )}
          {isError && (
            <ErrorBanner message={error?.message ?? 'Failed to load pending transactions'} onRetry={refetch} />
          )}
          {!isLoading && !isError && sorted.length === 0 && (
            <div className={styles.center}>No pending transactions</div>
          )}
          {!isLoading && !isError && sorted.map((tx) => (
            <ReviewCard
              key={tx.id}
              tx={tx}
              onViewDoc={(id) => setSelectedDocId(id === selectedDocId ? null : id)}
              isDocSelected={selectedDocId === tx.id}
            />
          ))}
        </div>
        <div className={styles.panel}>
          <DocumentPanel txId={selectedDocId} />
        </div>
      </div>
    </div>
  )
}
