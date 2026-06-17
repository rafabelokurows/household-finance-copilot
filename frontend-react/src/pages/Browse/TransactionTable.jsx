import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { getProcessed } from '../../api/transactions'
import { PAGE_SIZE } from '../../api/constants'
import TransactionRow from './TransactionRow'
import EditForm from './EditForm'
import Spinner from '../../components/shared/Spinner'
import ErrorBanner from '../../components/shared/ErrorBanner'
import styles from './TransactionTable.module.css'

const fmt = (n) =>
  new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(n)

export default function TransactionTable({ from, to, category }) {
  const { token } = useAuth()
  const [page, setPage] = useState(0)
  const [editingId, setEditingId] = useState(null)

  useEffect(() => { setPage(0) }, [from, to, category])

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['transactions', from, to, category, page],
    queryFn: () =>
      getProcessed(token, {
        date_from: from,
        date_to: to,
        category,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    enabled: !!token,
    keepPreviousData: true,
  })

  const transactions = data?.transactions ?? data ?? []
  const totalDebit = transactions
    .filter(tx => (tx.amount ?? 0) < 0)
    .reduce((sum, tx) => sum + Math.abs(tx.amount ?? 0), 0)

  if (isLoading) {
    return (
      <div className={styles.center}>
        <Spinner size={24} />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorBanner
        message={error?.message || 'Failed to load transactions'}
        onRetry={refetch}
      />
    )
  }

  const hasPrev = page > 0
  const hasNext = transactions.length === PAGE_SIZE

  return (
    <div className={styles.wrapper}>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Merchant</th>
            <th>Category</th>
            <th>Owner</th>
            <th className={styles.right}>Amount</th>
            <th className={styles.right}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(tx => (
            <React.Fragment key={tx.id}>
              <TransactionRow
                tx={tx}
                isEditing={editingId === tx.id}
                onEdit={() => setEditingId(editingId === tx.id ? null : tx.id)}
                onClose={() => setEditingId(null)}
              />
              {editingId === tx.id && (
                <tr className={styles.editRow}>
                  <td colSpan={6}>
                    <EditForm
                      tx={tx}
                      onClose={() => setEditingId(null)}
                      onSaved={() => setEditingId(null)}
                    />
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={4}>
              <span className={styles.footInfo}>
                {transactions.length} transactions &middot; {fmt(totalDebit)} spent
              </span>
            </td>
            <td colSpan={2}>
              <div className={styles.footActions}>
                <button
                  className={styles.pageBtn}
                  disabled={!hasPrev}
                  onClick={() => setPage(p => p - 1)}
                >
                  Prev
                </button>
                <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  {page + 1}
                </span>
                <button
                  className={styles.pageBtn}
                  disabled={!hasNext}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </button>
              </div>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
