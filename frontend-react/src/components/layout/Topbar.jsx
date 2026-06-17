import styles from './Topbar.module.css'

export default function Topbar({ title, children }) {
  return (
    <header className={styles.topbar}>
      <h1 className={styles.title}>{title}</h1>
      <div className={styles.controls}>{children}</div>
    </header>
  )
}
