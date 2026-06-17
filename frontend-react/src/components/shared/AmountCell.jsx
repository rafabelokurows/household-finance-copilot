import styles from './AmountCell.module.css'

export default function AmountCell({ amount, type }) {
  const isCredit = type === 'credit' || amount > 0
  const formatted = new Intl.NumberFormat('pt-PT', {
    style: 'currency',
    currency: 'EUR',
  }).format(Math.abs(amount ?? 0))

  return (
    <span className={`${styles.amount} mono ${isCredit ? styles.credit : styles.debit}`}>
      {isCredit ? '+' : '-'}{formatted}
    </span>
  )
}
