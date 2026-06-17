import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts'

export default function SparkLine({ data, dataKey = 'total' }) {
  if (!data?.length) return null
  return (
    <ResponsiveContainer width="100%" height={60}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#C9924A" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#C9924A" stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke="#C9924A"
          strokeWidth={1.5}
          fill="url(#sparkGrad)"
          dot={false}
          activeDot={{ r: 3, fill: '#C9924A' }}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            return (
              <div style={{
                background: 'var(--surface2)',
                border: '1px solid var(--border)',
                borderRadius: 4,
                padding: '4px 8px',
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                color: 'var(--gold)',
              }}>
                {new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(payload[0].value)}
              </div>
            )
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
