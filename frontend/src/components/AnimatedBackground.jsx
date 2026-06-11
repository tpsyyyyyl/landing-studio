const ORBS = [
  {
    color: 'var(--orb-1)',
    size: '28rem',
    style: { top: '-8rem', left: '15%' },
    animation: 'float-a 26s ease-in-out infinite alternate',
  },
  {
    color: 'var(--orb-2)',
    size: '24rem',
    style: { bottom: '-6rem', right: '10%' },
    animation: 'float-b 32s ease-in-out infinite alternate',
  },
  {
    color: 'var(--orb-3)',
    size: '20rem',
    style: { top: '38%', left: '55%' },
    animation: 'float-c 22s ease-in-out infinite alternate',
  },
]

export default function AnimatedBackground() {
  return (
    <>
      {ORBS.map((o, i) => (
        <div
          key={i}
          className="orb"
          style={{
            background: o.color,
            width: o.size,
            height: o.size,
            animation: o.animation,
            ...o.style,
          }}
        />
      ))}
    </>
  )
}
