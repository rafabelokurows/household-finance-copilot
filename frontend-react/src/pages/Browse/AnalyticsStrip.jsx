import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { getProcessed } from '../../api/transactions'
import { getByCategory, getTrends } from '../../api/analytics'
import DonutChart from '../../components/charts/DonutChart'
import SparkLine from '../../components/charts/SparkLine'
import Spinner from '../../components/shared/Spinner'
import ErrorBanner from '../../components/shared/ErrorBanner'
import styles from './AnalyticsStrip.module.css'

const CATEGORY_COLORS = [
  '#C9924A', '#6A9E72', '#5B8DB8', '#A67DB8', '#D4856A',
  '#7ABFBF', '#D4AF37', '#8B7355', '#6B9E6B', '#B85B5B',
  '#7B9EC9', '#C9A87A', '#9E7BAF',
]

const fmt = (n) =>
  new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(n)

export default function AnalyticsStrip({ from, to, category }) {
  const { token } = useAuth()

  const txQuery = useQuery({
    queryKey: ['transactions-all', from, to, category],
    queryFn: () => getProcessed(token, { date_from: from, date_to: to, category, limit: 9999 }),
    enabled: !!token,
  })

  const categoryQuery = useQuery({
    queryKey: ['by-category', from, to],
    queryFn: () => getByCategory(token, { date_from: from, date_to: to }),
    enabled: !!token,
  })

  const trendsQuery = useQuery({
    queryKey: ['trends', from, to],
    queryFn: () => getTrends(token, { from, to }),
    enabled: !!token,
  })

  if (txQuery.isLoading || categoryQuery.isLoading || trendsQuery.isLoading) {
    return (
      <div className={styles.center}>
        <Spinner size={20} />
      </div>
    )
  }

  if (txQuery.isError || categoryQuery.isError || trendsQuery.isError) {
    const err = txQuery.error || categoryQuery.error || trendsQuery.error
    return (
      <ErrorBanner
        message={err?.message || 'Failed to load analytics'}
        onRetry={() => {
          txQuery.refetch()
          categoryQuery.refetch()
          trendsQuery.refetch()
        }}
      />
    )
  }

  const transactions = txQuery.data?.transactions ?? txQuery.data ?? []

  const rawCategory = categoryQuery.data?.categories ?? []
  const categoryData = rawCategory.map((item) => ({
    category: item.name ?? item.category,
    total: Math.abs(item.amount ?? item.total ?? 0),
  }))

  const rawTrends = trendsQuery.data?.weeks ?? []
  const trendsData = rawTrends.map((item) => ({
    week: item.week_start,
    total: Math.abs(item.total_spending ?? item.total ?? 0),
  }))

  const INCOME_CATS = ['Salary', 'Bonus', 'Investments']

  const totalSpent = transactions
    .filter(tx => !INCOME_CATS.includes(tx.category))
    .reduce((sum, tx) => sum + (tx.amount ?? 0), 0)

  const totalIncome = transactions
    .filter(tx => INCOME_CATS.includes(tx.category))
    .reduce((sum, tx) => sum + (tx.amount ?? 0), 0)

  const txCount = transactions.length

  return (
    <div className={styles.strip}>
      <div className={styles.statBlock}>
        <div className={styles.statLabel}>Total Spent</div>
        <div className={styles.statValue} style={{ color: 'var(--red)' }}>
          {fmt(totalSpent)}
        </div>
      </div>

      <div className={styles.statBlock}>
        <div className={styles.statLabel}>Income</div>
        <div className={styles.statValue} style={{ color: 'var(--green)' }}>
          {fmt(totalIncome)}
        </div>
      </div>

      <div className={styles.statBlock}>
        <div className={styles.statLabel}>Transactions</div>
        <div className={styles.statValue}>{txCount}</div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>By Category</div>
        {categoryData.length > 0 && <DonutChart data={categoryData} />}
        <div>
          {categoryData.map((item, i) => (
            <div key={item.category} className={styles.legendRow}>
              <div
                className={styles.legendDot}
                style={{ background: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}
              />
              <span className={styles.legendLabel}>{item.category}</span>
              <span className={styles.legendAmount}>{fmt(item.total)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Weekly Trend</div>
        {trendsData.length > 0 && (
          <SparkLine data={trendsData} dataKey="total" />
        )}
      </div>
    </div>
  )
}
