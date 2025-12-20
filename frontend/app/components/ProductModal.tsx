'use client'

import { useEffect, useCallback } from 'react'
import { Product } from '../types'
import { useCart } from '../cart/CartContext'
import { formatPrice, formatRating, getImagePath } from '../formatting'

interface ProductModalProps {
  product: Product | null
  onClose: () => void
}

export default function ProductModal({ product, onClose }: ProductModalProps) {
  const { addToCart } = useCart()

  useEffect(() => {
    if (product) {
      const originalOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      return () => {
        document.body.style.overflow = originalOverflow
      }
    }
  }, [product])

  const handleAddToCart = useCallback(() => {
    if (product) {
      addToCart(product)
      onClose()
    }
  }, [product, addToCart, onClose])

  if (!product) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <div className="modal-body">
          <img src={getImagePath(product.image_path)} alt={product.name} className="modal-image" />
          <div className="modal-info">
            <h2 className="modal-title">{product.name}</h2>
            <span className="modal-category">{product.category}</span>
            <p className="modal-description">{product.description}</p>
            <div className="modal-details">
              <div className="modal-price">{formatPrice(product.price)}</div>
              <div className="modal-rating">
                <span className="star">⭐</span>
                <span>{formatRating(product.rating)}</span>
              </div>
            </div>
            <button className="btn-primary add-to-cart-btn" onClick={handleAddToCart}>
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

