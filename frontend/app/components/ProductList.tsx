'use client'

import { useState, useMemo } from 'react'
import { Product } from '../types'
import ProductGrid from './ProductGrid'
import CategoryFilter from './CategoryFilter'

interface ProductListProps {
  products: Product[]
}

export default function ProductList({ products }: ProductListProps) {
  const [selectedCategory, setSelectedCategory] = useState('')

  const categories = useMemo(() => {
    const unique = Array.from(new Set(products.map((p) => p.category)))
    return unique.sort()
  }, [products])

  const filteredProducts = useMemo(() => {
    if (!selectedCategory) return products
    return products.filter((p) => p.category === selectedCategory)
  }, [products, selectedCategory])

  return (
    <>
      <CategoryFilter
        categories={categories}
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
      />
      <ProductGrid products={filteredProducts} />
    </>
  )
}

