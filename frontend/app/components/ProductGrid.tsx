'use client'

import { useState, useCallback } from 'react'
import { Product } from '../types'
import ProductCard from './ProductCard'
import ProductModal from './ProductModal'

interface ProductGridProps {
  products: Product[]
}

export default function ProductGrid({ products }: ProductGridProps) {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)

  const handleCloseModal = useCallback(() => setSelectedProduct(null), [])

  return (
    <>
      <div className="products-grid">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onClick={() => setSelectedProduct(product)}
          />
        ))}
      </div>
      <ProductModal product={selectedProduct} onClose={handleCloseModal} />
    </>
  )
}
