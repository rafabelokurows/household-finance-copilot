import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { updateTransaction } from '../../api/transactions'
import { CATEGORIES, OWNERS } from '../../api/constants'
import styles from './EditForm.module.css'

export default function EditForm({ tx, onClose, onSaved }) {
  const { token } = useAuth()
  const queryClient = useQueryClient()

  const [merchant, setMerchant] = useState(tx.merchant ?? tx.description ?? '')
  const [amount, setAmount] = useState(tx.amount ?? '')
  const [description, setDescription] = useState(tx.description ?? '')
  const [owner, setOwner] = useState(tx.owner ?? '')
  const [category, setCategory] = useState(tx.category ?? '')

  const mutation = useMutation({
    mutationFn: () =>
      updateTransaction(token, tx.id, {
        merchant: merchant || null,
        amount: amount !== '' ? parseFloat(amount) : null,
        description: description || null,
        owner: owner || null,
        category: category || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transactions-all'] })
      queryClient.invalidateQueries({ queryKey: ['by-category'] })
      queryClient.invalidateQueries({ queryKey: ['trends'] })
      onClose()
      if (onSaved) onSaved()
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.field}>
        <label className={styles.label}>Merchant</label>
        <input
          type="text"
          value={merchant}
          onChange={e => setMerchant(e.target.value)}
        />
      </div>
      <div className={styles.field}>
        <label className={styles.label}>Amount</label>
        <input
          type="number"
          step="0.01"
          value={amount}
          onChange={e => setAmount(e.target.value)}
        />
      </div>
      <div className={styles.field}>
        <label className={styles.label}>Description</label>
        <input
          type="text"
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
      </div>
      <div className={styles.field}>
        <label className={styles.label}>Owner</label>
        <select value={owner} onChange={e => setOwner(e.target.value)}>
          {OWNERS.map(o => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>
      <div className={styles.field}>
        <label className={styles.label}>Category</label>
        <select value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">— None —</option>
          {CATEGORIES.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.cancelBtn}
          onClick={onClose}
          disabled={mutation.isPending}
        >
          Cancel
        </button>
        <button
          type="submit"
          className={styles.saveBtn}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  )
}
