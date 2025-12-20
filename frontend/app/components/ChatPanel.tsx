'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { ChatMessage, CartAction } from '../types'
import { sendChatMessage } from '../chat'
import { useCart } from '../cart/CartContext'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
}

export default function ChatPanel({ isOpen, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { addToCart, removeFromCart, updateQuantity, clearCart } = useCart()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: "Hi! I'm your shopping assistant. I can help you find products and answer questions. What are you looking for today?",
        timestamp: new Date(),
      }
      setMessages([welcomeMessage])
    }
  }, [isOpen, messages.length])

  const applyCartActions = useCallback((actions: CartAction[]) => {
    actions.forEach((action) => {
      switch (action.type) {
        case 'add':
          if (action.product) {
            addToCart(action.product)
          }
          break
        case 'remove':
          if (action.productId) {
            removeFromCart(action.productId)
          }
          break
        case 'update':
          if (action.productId !== undefined && action.quantity !== undefined) {
            updateQuantity(action.productId, action.quantity)
          }
          break
        case 'clear':
          clearCart()
          break
      }
    })
  }, [addToCart, removeFromCart, updateQuantity, clearCart])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendChatMessage(newMessages)
      
      const assistantMessage: ChatMessage = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
      }

      setMessages([...newMessages, assistantMessage])

      // Apply any cart actions from the agent
      if (response.cartActions && response.cartActions.length > 0) {
        applyCartActions(response.cartActions)
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages([...newMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <>
      <div className="chat-overlay" onClick={onClose} />
      <div className="chat-panel">
        <div className="chat-header">
          <h2>Shopping Assistant</h2>
          <button className="chat-close" onClick={onClose}>×</button>
        </div>
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`chat-message ${message.role}`}>
              <div className="chat-message-content">
                {message.content}
              </div>
              <div className="chat-message-time">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="chat-message assistant">
              <div className="chat-message-content">
                <span className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form className="chat-input-form" onSubmit={handleSend}>
          <input
            type="text"
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything about products..."
            disabled={isLoading}
          />
          <button type="submit" className="chat-send" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </>
  )
}

