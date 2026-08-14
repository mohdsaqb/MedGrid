export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <rect width="40" height="40" rx="10" fill="#2563EB" />
      <path
        d="M20 11v18M11 20h18"
        stroke="#FFFFFF"
        strokeWidth={4.2}
        strokeLinecap="round"
      />
      <circle cx="31" cy="9" r="3.4" fill="#22D3B8" />
    </svg>
  )
}
