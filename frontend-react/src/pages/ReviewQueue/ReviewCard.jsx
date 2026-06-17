import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { approveTransaction, rejectTransaction, updateTransaction, setTags } from '../../api/transactions'
import { CATEGORIES, OWNERS } from '../../api/constants'
import AmountCell from '../../components/shared/AmountCell'
import TagChip from '../../components/shared/TagChip'
import styles from './ReviewCard.module.css'

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('pt-PT', { day: '2-digit', month: 'short' })
}

function ConfidenceBadge({ value }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  const cls = value > 0.8 ? styles.confHigh : value > 0.5 ? styles.confMid : styles.confLow
  return <span className={`${styles.confidence} ${cls}`}>{pct}%</span>
}

export default function ReviewCard({ tx, onViewDoc, isDocSelected }) {
  const { token } = useAuth()
  const queryClient = useQueryClient()

  const [owner, setOwner] = useState(tx.owner ?? '')
  const [category, setCategory] = useState(tx.category ?? '')
  const [editOpen, setEditOpen] = useState(false)
  const [tagInput, setTagInput] = useState('')
  const [showTagInput, setShowTagInput] = useState(false)

  // Edit form local state
  const [editMerchant, setEditMerchant] = useState(tx.merchant ?? '')
  const [editAmount, setEditAmount] = useState(tx.amount ?? '')
  const [editDescription, setEditDescription] = useState(tx.description ?? '')

  const invalidatePending = () => queryClient.invalidateQueries({ queryKey: ['pending'] })

  const updateMut = useMutation({
    mutationFn: (fields) => updateTransaction(token, tx.id, fields),
    onSuccess: invalidatePending,
  })

  const approveMut = useMutation({
    mutationFn: async () => {
      await updateTransaction(token, tx.id, { owner, category })
      await approveTransaction(token, tx.id)
    },
    onSuccess: invalidatePending,
  })

  const rejectMut = useMutation({
    mutationFn: () => rejectTransaction(token, tx.id),
    onSuccess: invalidatePending,
  })

  const tagMut = useMutation({
    mutationFn: (newTags) => setTags(token, tx.id, newTags),
    onSuccess: invalidatePending,
  })

  function handleAddTag() {
    const tag = tagInput.trim()
    if (!tag) return
    const current = tx.tags ?? []
    if (!current.includes(tag)) tagMut.mutate([...current, tag])
    setTagInput('')
    setShowTagInput(false)
  }

  function handleRemoveTag(tag) {
    tagMut.mutate((tx.tags ?? []).filter(t => t !== tag))
  }

  function handleSaveEdit() {
    updateMut.mutate({
      merchant: editMerchant,
      amount: parseFloat(editAmount),
      description: editDescription,
    })
    setEditOpen(false)
  }

  function handleCancelEdit() {
    setEditMerchant(tx.merchant ?? '')
    setEditAmount(tx.amount ?? '')
    setEditDescription(tx.description ?? '')
    setEditOpen(false)
  }

  const busy = approveMut.isPending || rejectMut.isPending

  return (
    <div className={`${styles.card} ${isDocSelected ? styles.docSelected : ''}`}>
      {/* Header */}
      <div className={styles.header}>
        <span className={styles.date}>{formatDate(tx.date)}</span>
        <span className={styles.merchant}>{tx.merchant}</span>
        <AmountCell amount={tx.amount} type={tx.amount < 0 ? 'debit' : 'credit'} />
        <ConfidenceBadge value={tx.confidence} />
      </div>

      {/* Meta row */}
      <div className={styles.meta}>
        <span className={styles.bank}>{tx.bank_name ?? tx.bank ?? ''}</span>
        <select
          className={styles.metaSelect}
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">— category —</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          className={styles.metaSelect}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
        >
          <option value="">— owner —</option>
          {OWNERS.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>

      {/* Tags */}
      {((tx.tags && tx.tags.length > 0) || showTagInput) && (
        <div className={styles.tags}>
          {(tx.tags ?? []).map((tag) => (
            <TagChip key={tag} tag={tag} onRemove={() => handleRemoveTag(tag)} />
          ))}
          {showTagInput && (
            <input
              className={styles.tagInput}
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleAddTag(); if (e.key === 'Escape') setShowTagInput(false) }}
              autoFocus
              placeholder="tag…"
            />
          )}
        </div>
      )}

      {/* Description */}
      {tx.description && (
        <div className={styles.description}>{tx.description}</div>
      )}

      {/* Actions */}
      <div className={styles.actions}>
        <button
          className={styles.approveBtn}
          onClick={() => approveMut.mutate()}
          disabled={busy}
        >
          ✓ Approve
        </button>
        <button
          className={styles.rejectBtn}
          onClick={() => rejectMut.mutate()}
          disabled={busy}
        >
          ✗ Reject
        </button>
        {tx.document_id && (
          <button
            className={`${styles.docBtn} ${isDocSelected ? styles.active : ''}`}
            onClick={() => onViewDoc(tx.id)}
          >
            📄 Doc
          </button>
        )}
        <button
          className={styles.addTagBtn}
          onClick={() => setShowTagInput((v) => !v)}
        >
          + tag
        </button>
        <button
          className={`${styles.editBtn} ${editOpen ? styles.active : ''}`}
          onClick={() => setEditOpen((v) => !v)}
        >
          Edit
        </button>
      </div>

      {/* Inline edit form */}
      {editOpen && (
        <div className={styles.editForm}>
          <div className={styles.editField}>
            <label className={styles.editLabel}>Merchant</label>
            <input
              value={editMerchant}
              onChange={(e) => setEditMerchant(e.target.value)}
            />
          </div>
          <div className={styles.editField}>
            <label className={styles.editLabel}>Amount</label>
            <input
              type="number"
              value={editAmount}
              onChange={(e) => setEditAmount(e.target.value)}
            />
          </div>
          <div className={styles.editField}>
            <label className={styles.editLabel}>Description</label>
            <input
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
            />
          </div>
          <div className={styles.editActions}>
            <button className={styles.cancelBtn} onClick={handleCancelEdit}>Cancel</button>
            <button
              className={styles.saveBtn}
              onClick={handleSaveEdit}
              disabled={updateMut.isPending}
            >
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
