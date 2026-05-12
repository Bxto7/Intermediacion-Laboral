interface Props { fullScreen?: boolean; size?: 'sm' | 'md' | 'lg' }

export const LoadingSpinner: React.FC<Props> = ({ fullScreen, size = 'md' }) => {
  const sizes = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-12 w-12' }
  const spinner = (
    <div className={`${sizes[size]} animate-spin rounded-full border-[3px] border-warm-200 border-t-primary-600`} />
  )
  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-warm-50/90 z-50">
        {spinner}
      </div>
    )
  }
  return <div className="flex justify-center items-center p-4">{spinner}</div>
}
