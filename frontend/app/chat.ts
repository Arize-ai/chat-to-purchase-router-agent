import { ChatMessage, CartAction } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatResponse {
  message: string
  cartActions?: CartAction[]
}

let sessionIdInitialized = false

function getSessionId(): string {
  if (typeof window === 'undefined') return ''
  
  if (!sessionIdInitialized) {
    sessionStorage.removeItem('chat_session_id')
    sessionIdInitialized = true
  }
  
  let sessionId = sessionStorage.getItem('chat_session_id')
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    sessionStorage.setItem('chat_session_id', sessionId)
  }
  return sessionId
}

export async function sendChatMessage(
  messages: ChatMessage[]
): Promise<ChatResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000)

  const lastUserMessage = messages.filter(m => m.role === 'user').pop()
  if (!lastUserMessage) {
    throw new Error('No user message found')
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: lastUserMessage.content,
        sessionId: getSessionId(),
      }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Chat API error: ${response.status} ${response.statusText} - ${errorText}`)
    }

    const data = await response.json()
    
    if (!data || !data.message) {
      throw new Error('Invalid response from server: ' + JSON.stringify(data))
    }
    
    return {
      message: data.message,
      cartActions: data.cartActions || [],
    }
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.')
    }
    throw error
  }
}

