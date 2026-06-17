import { NavLink } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import styles from './Sidebar.module.css'

const NAV = [
  { to: '/browse', label: 'Browse', icon: '◧' },
  { to: '/analytics', label: 'Analytics', icon: '◬' },
  { to: '/review', label: 'Review Queue', icon: '◈', badge: true },
  { to: '/statements', label: 'Statements', icon: '◫' },
  { to: '/rules', label: 'Rules', icon: '◱' },
]

export default function Sidebar({ pendingCount }) {
  const { username, logout } = useAuth()

  return (
    <nav className={styles.sidebar}>
      <div className={styles.logo}>
        <span className={styles.logoIcon}>◈</span>
        <span className={styles.logoText}>Household Finance Copilot</span>
      </div>

      <ul className={styles.nav}>
        {NAV.map(({ to, label, icon, badge }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
            >
              <span className={styles.navIcon}>{icon}</span>
              <span className={styles.navLabel}>{label}</span>
              {badge && pendingCount > 0 && (
                <span className={styles.badge}>{pendingCount}</span>
              )}
            </NavLink>
          </li>
        ))}
      </ul>

      <div className={styles.footer}>
        <span className={styles.username}>{username}</span>
        <button className={styles.logoutBtn} onClick={logout} title="Sign out">
          ⎋
        </button>
      </div>
    </nav>
  )
}
