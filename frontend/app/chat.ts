import { ChatMessage, CartAction } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatResponse {
  message: string
  cartActions?: CartAction[]
}

export async function sendChatMessage(
  messages: ChatMessage[]
): Promise<ChatResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
      }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.statusText}`)
    }

    const data = await response.json()
    return {
      message: data.message || data.response || 'Sorry, I encountered an error.',
      cartActions: data.cartActions || [],
    }
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.')
    }
    console.error('Error sending chat message:', error)
    throw error
  }
}

