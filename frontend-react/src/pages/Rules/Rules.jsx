import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../auth/AuthContext'
import { getRules } from '../../api/categories'
import { CATEGORIES } from '../../api/constants'
import Topbar from '../../components/layout/Topbar'
import RuleCategory from './RuleCategory'
import Spinner from '../../components/shared/Spinner'
import ErrorBanner from '../../components/shared/ErrorBanner'
import styles from './Rules.module.css'

export default function Rules() {
  const { token } = useAuth()

  const { data: rules, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['rules'],
    queryFn: () => getRules(token),
  })

  return (
    <div className={styles.page}>
      <Topbar title="Rules" />
      <div className={styles.content}>
        {isLoading ? (
          <div className={styles.center}>
            <Spinner size={20} />
          </div>
        ) : isError ? (
          <ErrorBanner message={error?.message || 'Failed to load rules'} onRetry={refetch} />
        ) : (
          (() => {
            const rulesMap = (rules ?? []).reduce(
              (acc, r) => ({ ...acc, [r.category]: r.keywords }),
              {}
            )
            return CATEGORIES.map((category) => (
              <RuleCategory
                key={category}
                category={category}
                keywords={rulesMap[category] ?? []}
                token={token}
              />
            ))
          })()
        )}
      </div>
    </div>
  )
}
