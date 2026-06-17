import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { setTags } from '../../api/transactions'
import CategoryPill from '../../components/shared/CategoryPill'
import TagChip from '../../components/shared/TagChip'
import AmountCell from '../../components/shared/AmountCell'
import styles from './TransactionRow.module.css'

const fmtDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('pt-PT', {
    day: '2-digit',
    month: 'short',
  })
}

export default function TransactionRow({ tx, isEditing, onEdit }) {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [showTagInput, setShowTagInput] = useState(false)
  const [tagValue, setTagValue] = useState('')

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
    queryClient.invalidateQueries({ queryKey: ['transactions-all'] })
  }

  const tagMutation = useMutation({
    mutationFn: (newTags) => setTags(token, tx.id, newTags),
    onSuccess: invalidate,
  })

  function handleRemoveTag(tag) {
    tagMutation.mutate((tx.tags ?? []).filter(t => t !== tag))
  }

  function handleAddTag() {
    const trimmed = tagValue.trim()
    if (!trimmed) return
    const current = tx.tags ?? []
    if (!current.includes(trimmed)) {
      tagMutation.mutate([...current, trimmed])
    }
    setTagValue('')
    setShowTagInput(false)
  }

  function handleTagKeyDown(e) {
    if (e.key === 'Enter') handleAddTag()
    if (e.key === 'Escape') {
      setShowTagInput(false)
      setTagValue('')
    }
  }

  return (
    <tr className={`${styles.row} ${isEditing ? styles.selected : ''}`}>
      <td className={styles.date}>{fmtDate(tx.date)}</td>
      <td>
        <div className={styles.merchant}>{tx.merchant ?? tx.description ?? '—'}</div>
        {tx.bank && <div className={styles.bank}>{tx.bank}</div>}
        {(tx.tags?.length > 0 || showTagInput) && (
          <div className={styles.tags}>
            {(tx.tags ?? []).map(tag => (
              <TagChip
                key={tag}
                tag={tag}
                onRemove={() => handleRemoveTag(tag)}
              />
            ))}
            {showTagInput ? (
              <input
                autoFocus
                className={styles.tagInput}
                value={tagValue}
                onChange={e => setTagValue(e.target.value)}
                onKeyDown={handleTagKeyDown}
                onBlur={() => {
                  if (!tagValue.trim()) {
                    setShowTagInput(false)
                  }
                }}
                placeholder="tag name"
              />
            ) : (
              <button
                className={styles.addTagBtn}
                onClick={() => setShowTagInput(true)}
              >
                +
              </button>
            )}
          </div>
        )}
        {!tx.tags?.length && !showTagInput && (
          <div className={styles.tags}>
            <button
              className={styles.addTagBtn}
              onClick={() => setShowTagInput(true)}
            >
              + tag
            </button>
          </div>
        )}
      </td>
      <td>
        {tx.category && <CategoryPill category={tx.category} />}
      </td>
      <td className={styles.owner}>{tx.owner ?? '—'}</td>
      <td className={styles.amount}>
        <AmountCell amount={tx.amount} type={tx.type} />
      </td>
      <td className={styles.actions}>
        <button
          className={`${styles.editBtn} ${isEditing ? styles.active : ''}`}
          onClick={onEdit}
          title="Edit"
        >
          ✎
        </button>
      </td>
    </tr>
  )
}
