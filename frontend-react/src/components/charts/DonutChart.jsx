import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = [
  '#C9924A', '#4A8C5C', '#5C7A8C', '#7A5C8C', '#8C7A4A',
  '#8C5C7A', '#4A6A8C', '#6A8C4A', '#8C6A4A', '#4A8C6A',
  '#8C8C4A', '#4A7A8C', '#5A5A5A',
]

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0].payload
  return (
    <div style={{
      background: 'var(--surface2)',
      border: '1px solid var(--border)',
      borderRadius: 4,
      padding: '6px 10px',
      fontSize: 12,
      color: 'var(--text)',
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>{name}</div>
      <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--gold)' }}>
        {new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(value)}
      </div>
    </div>
  )
}

export default function DonutChart({ data }) {
  if (!data?.length) return null

  const chartData = data.map(d => ({ name: d.category ?? d.name, value: Math.abs(d.total ?? d.value ?? 0) }))

  return (
    <ResponsiveContainer width="100%" height={180}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={52}
          outerRadius={80}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="none" />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  )
}
