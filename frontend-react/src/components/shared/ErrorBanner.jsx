import styles from './ErrorBanner.module.css'

export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className={styles.banner}>
      <span>{message || 'Something went wrong'}</span>
      {onRetry && (
        <button className={styles.retry} onClick={onRetry}>Retry</button>
      )}
    </div>
  )
}
