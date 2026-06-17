import { useMemo, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import Topbar from '../../components/layout/Topbar'
import ErrorBanner from '../../components/shared/ErrorBanner'
import Spinner from '../../components/shared/Spinner'
import { useAuth } from '../../auth/AuthContext'
import {
  getByCategory,
  getByMonth,
  getByOwner,
  getByTag,
  getCategoryTrends,
  getTrends,
} from '../../api/analytics'
import styles from './Analytics.module.css'

const COLORS = [
  '#C9924A',
  '#4A8C5C',
  '#5C7A8C',
  '#7A5C8C',
  '#8C7A4A',
  '#8C5C7A',
  '#4A6A8C',
  '#6A8C4A',
  '#8C6A4A',
  '#4A8C6A',
  '#8C8C4A',
  '#4A7A8C',
  '#5A5A5A',
]

const fmtCurrency = (value = 0) =>
  new Intl.NumberFormat('pt-PT', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)

const axisStyle = {
  stroke: 'var(--text-dim)',
  fontSize: 11,
  fontFamily: 'var(--font-mono)',
}

function buildParams(fromDate, toDate) {
  return {
    date_from: fromDate || undefined,
    date_to: toDate || undefined,
  }
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  return (
    <div className={styles.tooltip}>
      {label && <div className={styles.tooltipLabel}>{label}</div>}
      {payload.map((item) => (
        <div key={item.name || item.dataKey} className={styles.tooltipRow}>
          <span
            className={styles.tooltipDot}
            style={{ background: item.color || item.fill }}
          />
          <span>{item.name}</span>
          <strong>{fmtCurrency(Math.abs(item.value ?? 0))}</strong>
        </div>
      ))}
    </div>
  )
}

function ChartCard({ title, subtitle, children, isEmpty }) {
  return (
    <section className={styles.card}>
      <div className={styles.cardHeader}>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {isEmpty ? (
        <div className={styles.empty}>No data for this view</div>
      ) : (
        children
      )}
    </section>
  )
}

export default function Analytics() {
  const { token } = useAuth()
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [monthWindow, setMonthWindow] = useState(12)

  const dateParams = useMemo(() => buildParams(fromDate, toDate), [fromDate, toDate])

  const categoryQuery = useQuery({
    queryKey: ['analytics-category', dateParams],
    queryFn: () => getByCategory(token, dateParams),
    enabled: !!token,
  })

  const tagQuery = useQuery({
    queryKey: ['analytics-tags', dateParams],
    queryFn: () => getByTag(token, dateParams),
    enabled: !!token,
  })

  const ownerQuery = useQuery({
    queryKey: ['analytics-owner', dateParams],
    queryFn: () => getByOwner(token, dateParams),
    enabled: !!token,
  })

  const trendsQuery = useQuery({
    queryKey: ['analytics-weekly', monthWindow],
    queryFn: () => getTrends(token, { weeks: monthWindow === 24 ? 24 : 12 }),
    enabled: !!token,
  })

  const monthQuery = useQuery({
    queryKey: ['analytics-months', monthWindow],
    queryFn: () => getByMonth(token, { months: monthWindow }),
    enabled: !!token,
  })

  const categoryTrendsQuery = useQuery({
    queryKey: ['analytics-category-trends', monthWindow],
    queryFn: () => getCategoryTrends(token, { months: Math.min(monthWindow, 24) }),
    enabled: !!token,
  })

  const queries = [
    categoryQuery,
    tagQuery,
    ownerQuery,
    trendsQuery,
    monthQuery,
    categoryTrendsQuery,
  ]
  const isLoading = queries.some((query) => query.isLoading)
  const errorQuery = queries.find((query) => query.isError)

  const categoryData = useMemo(
    () =>
      (categoryQuery.data?.categories ?? []).map((item) => ({
        name: item.name,
        total: Math.abs(item.amount ?? 0),
      })),
    [categoryQuery.data],
  )

  const tagData = useMemo(
    () =>
      (tagQuery.data?.tags ?? []).map((item) => ({
        name: item.name,
        total: Math.abs(item.amount ?? 0),
      })),
    [tagQuery.data],
  )

  const ownerData = useMemo(
    () =>
      (ownerQuery.data?.owners ?? []).map((item) => ({
        name: item.owner || 'Unassigned',
        total: Math.abs(item.total ?? 0),
      })),
    [ownerQuery.data],
  )

  const weeklyData = useMemo(
    () =>
      (trendsQuery.data?.weeks ?? []).map((item) => ({
        name: item.week_start,
        total: Math.abs(item.total_spending ?? 0),
      })),
    [trendsQuery.data],
  )

  const monthData = useMemo(
    () =>
      (monthQuery.data?.months ?? []).map((item) => ({
        name: item.month,
        total: Math.abs(item.total ?? 0),
      })),
    [monthQuery.data],
  )

  const stacked = useMemo(() => {
    const rows = categoryTrendsQuery.data?.trends ?? []
    const totals = new Map()
    rows.forEach((row) => {
      totals.set(row.category, (totals.get(row.category) ?? 0) + Math.abs(row.total ?? 0))
    })
    const topCategories = [...totals.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([name]) => name)

    const byMonth = new Map()
    rows.forEach((row) => {
      if (!topCategories.includes(row.category)) return
      const item = byMonth.get(row.month) ?? { name: row.month }
      item[row.category] = Math.abs(row.total ?? 0)
      byMonth.set(row.month, item)
    })

    return {
      categories: topCategories,
      months: [...byMonth.values()].sort((a, b) => a.name.localeCompare(b.name)),
    }
  }, [categoryTrendsQuery.data])

  const totalSpent = categoryData.reduce((sum, item) => sum + item.total, 0)
  const biggestCategory = categoryData[0]?.name ?? 'None'
  const monthlyAverage = monthData.length
    ? monthData.reduce((sum, item) => sum + item.total, 0) / monthData.length
    : 0

  function refetchAll() {
    queries.forEach((query) => query.refetch())
  }

  return (
    <div className={styles.page}>
      <Topbar title="Analytics">
        <div className={styles.filters}>
          <input
            type="date"
            className={styles.filterInput}
            value={fromDate}
            onChange={(event) => setFromDate(event.target.value)}
            aria-label="From date"
          />
          <input
            type="date"
            className={styles.filterInput}
            value={toDate}
            onChange={(event) => setToDate(event.target.value)}
            aria-label="To date"
          />
          <select
            className={styles.filterInput}
            value={monthWindow}
            onChange={(event) => setMonthWindow(Number(event.target.value))}
            aria-label="Month window"
          >
            <option value={6}>6 months</option>
            <option value={12}>12 months</option>
            <option value={24}>24 months</option>
          </select>
        </div>
      </Topbar>

      <main className={styles.content}>
        {isLoading && (
          <div className={styles.center}>
            <Spinner size={24} />
          </div>
        )}

        {errorQuery && (
          <ErrorBanner
            message={errorQuery.error?.message || 'Failed to load analytics'}
            onRetry={refetchAll}
          />
        )}

        {!isLoading && !errorQuery && (
          <>
            <div className={styles.summaryGrid}>
              <div className={styles.summaryItem}>
                <span>Total spending</span>
                <strong>{fmtCurrency(totalSpent)}</strong>
              </div>
              <div className={styles.summaryItem}>
                <span>Monthly average</span>
                <strong>{fmtCurrency(monthlyAverage)}</strong>
              </div>
              <div className={styles.summaryItem}>
                <span>Top category</span>
                <strong>{biggestCategory}</strong>
              </div>
            </div>

            <div className={styles.grid}>
              <ChartCard
                title="Spending per Category"
                subtitle="Approved transactions grouped by category"
                isEmpty={!categoryData.length}
              >
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      dataKey="total"
                      nameKey="name"
                      innerRadius={78}
                      outerRadius={118}
                      paddingAngle={2}
                    >
                      {categoryData.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className={styles.legendList}>
                  {categoryData.slice(0, 8).map((item, index) => (
                    <div key={item.name} className={styles.legendRow}>
                      <span
                        className={styles.legendDot}
                        style={{ background: COLORS[index % COLORS.length] }}
                      />
                      <span>{item.name}</span>
                      <strong>{fmtCurrency(item.total)}</strong>
                    </div>
                  ))}
                </div>
              </ChartCard>

              <ChartCard
                title="Spending per Month"
                subtitle={`Last ${monthWindow} months`}
                isEmpty={!monthData.length}
              >
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={monthData} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
                    <CartesianGrid stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={axisStyle} axisLine={false} tickLine={false} />
                    <YAxis tick={axisStyle} axisLine={false} tickLine={false} width={64} />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="total" name="Spending" fill="var(--gold)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard
                title="Weekly Trend"
                subtitle="Rolling weekly totals"
                isEmpty={!weeklyData.length}
              >
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={weeklyData} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
                    <defs>
                      <linearGradient id="weeklyTotal" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#C9924A" stopOpacity={0.32} />
                        <stop offset="100%" stopColor="#C9924A" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={axisStyle} axisLine={false} tickLine={false} />
                    <YAxis tick={axisStyle} axisLine={false} tickLine={false} width={64} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="total"
                      name="Spending"
                      stroke="var(--gold)"
                      strokeWidth={2}
                      fill="url(#weeklyTotal)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard
                title="Category Trends"
                subtitle="Top categories across recent months"
                isEmpty={!stacked.months.length}
              >
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={stacked.months} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
                    <CartesianGrid stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" tick={axisStyle} axisLine={false} tickLine={false} />
                    <YAxis tick={axisStyle} axisLine={false} tickLine={false} width={64} />
                    <Tooltip content={<ChartTooltip />} />
                    <Legend wrapperStyle={{ fontSize: 11, color: 'var(--text-muted)' }} />
                    {stacked.categories.map((name, index) => (
                      <Bar
                        key={name}
                        dataKey={name}
                        stackId="category"
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard
                title="Spending by Owner"
                subtitle="Household split for the selected dates"
                isEmpty={!ownerData.length}
              >
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={ownerData} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
                    <CartesianGrid stroke="var(--border)" horizontal={false} />
                    <XAxis type="number" tick={axisStyle} axisLine={false} tickLine={false} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={axisStyle}
                      axisLine={false}
                      tickLine={false}
                      width={84}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="total" name="Spending" radius={[0, 4, 4, 0]}>
                      {ownerData.map((_, index) => (
                        <Cell key={index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard
                title="Spending by Tag"
                subtitle="Tagged transactions for the selected dates"
                isEmpty={!tagData.length}
              >
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart
                    data={tagData.slice(0, 10)}
                    layout="vertical"
                    margin={{ top: 4, right: 16, left: 4, bottom: 0 }}
                  >
                    <CartesianGrid stroke="var(--border)" horizontal={false} />
                    <XAxis type="number" tick={axisStyle} axisLine={false} tickLine={false} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={axisStyle}
                      axisLine={false}
                      tickLine={false}
                      width={96}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <Bar dataKey="total" name="Spending" fill="var(--gold)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
