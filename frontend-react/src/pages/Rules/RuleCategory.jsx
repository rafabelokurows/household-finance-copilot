import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { addKeyword, deleteKeyword } from '../../api/categories'
import styles from './RuleCategory.module.css'

export default function RuleCategory({ category, keywords, token }) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')

  const addMutation = useMutation({
    mutationFn: (keyword) => addKeyword(token, category, keyword),
    onSuccess: () => {
      setInput('')
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (keyword) => deleteKeyword(token, category, keyword),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  function handleAdd() {
    const trimmed = input.trim()
    if (!trimmed) return
    addMutation.mutate(trimmed)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleAdd()
  }

  return (
    <div className={styles.section}>
      <div className={styles.header} onClick={() => setOpen((v) => !v)}>
        <span className={`${styles.chevron} ${open ? styles.open : ''}`}>▸</span>
        <span className={styles.catName}>{category}</span>
        <span className={styles.badge}>{keywords.length}</span>
      </div>

      {open && (
        <div className={styles.body}>
          {keywords.length === 0 ? (
            <div className={styles.empty}>No keywords yet</div>
          ) : (
            <div className={styles.pills}>
              {keywords.map((kw) => (
                <span key={kw} className={styles.pill}>
                  {kw}
                  <button
                    className={styles.deleteBtn}
                    onClick={() => deleteMutation.mutate(kw)}
                    disabled={deleteMutation.isPending}
                    aria-label={`Remove ${kw}`}
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          )}
          <div className={styles.addRow}>
            <input
              className={styles.addInput}
              type="text"
              placeholder="New keyword…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className={styles.addBtn}
              onClick={handleAdd}
              disabled={!input.trim() || addMutation.isPending}
            >
              {addMutation.isPending ? '…' : 'Add'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
