import styles from './CategoryPill.module.css'

const CATEGORY_COLORS = {
  Groceries: '#4A8C5C',
  Restaurants: '#C9924A',
  Transportation: '#5C7A8C',
  Utilities: '#7A5C8C',
  Shopping: '#8C7A4A',
  Entertainment: '#8C5C7A',
  Healthcare: '#4A6A8C',
  Travel: '#6A8C4A',
  Insurance: '#8C6A4A',
  Salary: '#4A8C6A',
  Bonus: '#8C8C4A',
  Investments: '#4A7A8C',
  Other: '#5A5A5A',
}

export default function CategoryPill({ category }) {
  const color = CATEGORY_COLORS[category] ?? '#5A5A5A'
  return (
    <span
      className={styles.pill}
      style={{ '--pill-color': color }}
    >
      {category ?? 'Uncategorized'}
    </span>
  )
}
