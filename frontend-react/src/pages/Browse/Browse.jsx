import { useState } from 'react'
import styles from './Browse.module.css'
import Topbar from '../../components/layout/Topbar'
import AnalyticsStrip from './AnalyticsStrip'
import TransactionTable from './TransactionTable'
import { exportCsv } from '../../api/transactions'
import { useAuth } from '../../auth/AuthContext'
import { CATEGORIES } from '../../api/constants'

export default function Browse() {
  const { token } = useAuth()
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [category, setCategory] = useState('')

  function handleExport() {
    exportCsv(token, { date_from: fromDate, date_to: toDate, category })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Topbar title="Browse">
        <div className={styles.filters}>
          <input
            type="date"
            className={styles.filterInput}
            value={fromDate}
            onChange={e => setFromDate(e.target.value)}
          />
          <input
            type="date"
            className={styles.filterInput}
            value={toDate}
            onChange={e => setToDate(e.target.value)}
          />
          <select
            className={styles.filterInput}
            value={category}
            onChange={e => setCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <button className={styles.exportBtn} onClick={handleExport}>
            Export CSV
          </button>
        </div>
      </Topbar>
      <div className={styles.body}>
        <div className={styles.strip}>
          <AnalyticsStrip from={fromDate} to={toDate} category={category} />
        </div>
        <div className={styles.table}>
          <TransactionTable from={fromDate} to={toDate} category={category} />
        </div>
      </div>
    </div>
  )
}
