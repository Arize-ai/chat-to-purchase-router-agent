export interface Product {
  id: number
  name: string
  description: string
  price: number
  rating: number
  category: string
  image_path: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface CartAction {
  type: 'add' | 'remove' | 'update' | 'clear'
  productId?: number
  quantity?: number
  product?: Product
}

