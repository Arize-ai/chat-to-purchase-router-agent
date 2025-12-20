'use client'

import { useMemo, useState, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { useCart } from '../cart/CartContext'
import ChatPanel from './ChatPanel'

interface HeaderProps {
  title: string
}

export default function Header({ title }: HeaderProps) {
  const { getItemCount } = useCart()
  const count = useMemo(() => getItemCount(), [getItemCount])
  const pathname = usePathname()
  const [isChatOpen, setIsChatOpen] = useState(false)

  useEffect(() => {
    setIsChatOpen(pathname === '/')
  }, [pathname])

  return (
    <>
      <div className="header">
        <h1>{title}</h1>
        <div className="header-actions">
          <button className="chat-toggle" onClick={() => setIsChatOpen(!isChatOpen)}>
            💬 Chat Assistant
          </button>
          <Link href="/cart" className="cart-icon">
            <span>🛒 Your Items</span>
            {count > 0 && <span className="cart-badge">{count}</span>}
          </Link>
        </div>
      </div>
      <ChatPanel isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </>
  )
}

