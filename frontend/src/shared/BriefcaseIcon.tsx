/* SVG inline — maleta / briefcase para branding DRTPE */
export const BriefcaseIcon: React.FC<{ className?: string }> = ({ className = 'w-8 h-8' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.75}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    aria-hidden="true"
  >
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
    <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
    <line x1="12" y1="12" x2="12" y2="12" />
    <path d="M2 12h20" />
  </svg>
)

export const BriefcaseFilled: React.FC<{ className?: string }> = ({ className = 'w-8 h-8' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
    aria-hidden="true"
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M7 5a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v1h2a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h2V5zm2 1h6V5a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v1zm-2 2H5a1 1 0 0 0-1 1v2.5h16V9a1 1 0 0 0-1-1h-2H7zm-3 5v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4H4z"
    />
  </svg>
)
