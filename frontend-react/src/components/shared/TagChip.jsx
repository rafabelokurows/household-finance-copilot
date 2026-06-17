import styles from './TagChip.module.css'

export default function TagChip({ tag, onRemove }) {
  return (
    <span className={styles.chip}>
      {tag}
      {onRemove && (
        <button className={styles.remove} onClick={() => onRemove(tag)} aria-label={`Remove tag ${tag}`}>
          ×
        </button>
      )}
    </span>
  )
}
