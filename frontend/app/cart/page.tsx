'use client'

import { useMemo, useCallback } from 'react'
import Link from 'next/link'
import { useCart } from './CartContext'
import Header from '../components/Header'
import { formatPrice, getImagePath } from '../formatting'

export default function CartPage() {
  const { cart, removeFromCart, updateQuantity, clearCart, getTotal, getItemCount } = useCart()

  const total = useMemo(() => getTotal(), [getTotal])

  const handleDecreaseQuantity = useCallback(
    (id: number, currentQuantity: number) => {
      updateQuantity(id, currentQuantity - 1)
    },
    [updateQuantity]
  )

  const handleIncreaseQuantity = useCallback(
    (id: number, currentQuantity: number) => {
      updateQuantity(id, currentQuantity + 1)
    },
    [updateQuantity]
  )

  if (cart.length === 0) {
    return (
      <div className="container">
        <Header title="Shopping Cart" />
        <div className="empty-cart">
          <p>Your cart is empty</p>
          <Link href="/" className="btn-primary back-link">Continue Shopping</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <Header title="Shopping Cart" />

      <div className="cart-items">
        {cart.map((item) => (
          <div key={item.id} className="cart-item">
            <img src={getImagePath(item.image_path)} alt={item.name} className="cart-item-image" />
            <div className="cart-item-info">
              <h3 className="cart-item-name">{item.name}</h3>
              <span className="cart-item-category">{item.category}</span>
              <div className="cart-item-price">{formatPrice(item.price)}</div>
            </div>
            <div className="cart-item-controls">
              <div className="quantity-controls">
                <button onClick={() => handleDecreaseQuantity(item.id, item.quantity)}>-</button>
                <span>{item.quantity}</span>
                <button onClick={() => handleIncreaseQuantity(item.id, item.quantity)}>+</button>
              </div>
              <button className="remove-btn" onClick={() => removeFromCart(item.id)}>Remove</button>
            </div>
            <div className="cart-item-total">{formatPrice(item.price * item.quantity)}</div>
          </div>
        ))}
      </div>

      <div className="cart-summary">
        <div className="cart-total">
          <strong>Total: {formatPrice(total)}</strong>
        </div>
        <div className="cart-actions">
          <button className="btn-secondary clear-cart-btn" onClick={clearCart}>Clear Cart</button>
          <Link href="/" className="btn-primary continue-shopping-btn">Continue Shopping</Link>
        </div>
      </div>
    </div>
  )
}

