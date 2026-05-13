interface Props { fullScreen?: boolean; size?: 'sm' | 'md' | 'lg' }

export const LoadingSpinner: React.FC<Props> = ({ fullScreen, size = 'md' }) => {
  const sizes = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-12 w-12' }
  const spinner = (
    <div
      className={`${sizes[size]} animate-spin rounded-full border-[3px]`}
      style={{ borderColor: 'var(--bg-warm)', borderTopColor: 'var(--terra-500)' }}
    />
  )
  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center z-50" style={{ background: 'rgba(247,241,232,0.88)', backdropFilter: 'blur(8px)' }}>
        {spinner}
      </div>
    )
  }
  return <div className="flex justify-center items-center p-6">{spinner}</div>
}
