'use client'

import { memo, useMemo } from 'react'
import { Product } from '../types'
import { formatPrice, formatRating, getImagePath, truncateText } from '../formatting'

interface ProductCardProps {
  product: Product
  onClick: () => void
}

function ProductCard({ product, onClick }: ProductCardProps) {
  const truncatedDesc = useMemo(
    () => truncateText(product.description || '', 100),
    [product.description]
  )
  
  return (
    <div className="product-card" onClick={onClick}>
      <img src={getImagePath(product.image_path)} alt={product.name} className="product-image" />
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        <span className="product-category">{product.category}</span>
        {truncatedDesc && (
          <p className="product-description">{truncatedDesc}</p>
        )}
        <div className="product-details">
          <div className="product-price">{formatPrice(product.price)}</div>
          <div className="product-rating">
            <span className="star">⭐</span>
            <span>{formatRating(product.rating)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default memo(ProductCard)

