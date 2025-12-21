import { ChatMessage, CartAction } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ChatResponse {
  message: string
  cartActions?: CartAction[]
}

// Store session ID in sessionStorage
function getSessionId(): string {
  if (typeof window === 'undefined') return ''
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
  const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

  // Get the last user message
  const lastUserMessage = messages.filter(m => m.role === 'user').pop()
  if (!lastUserMessage) {
    throw new Error('No user message found')
  }

  try {
    console.log('Sending message to:', `${API_BASE_URL}/api/chat`)
    console.log('Message:', lastUserMessage.content)
    console.log('SessionId:', getSessionId())
    
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

    console.log('Response status:', response.status, response.statusText)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error Response:', errorText)
      throw new Error(`Chat API error: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    console.log('API Response:', data) // Debug log
    
    if (!data || !data.message) {
      console.error('No message in API response:', data)
      throw new Error('Invalid response from server: ' + JSON.stringify(data))
    }
    
    return {
      message: data.message,
      cartActions: data.cartActions || [],
    }
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      console.error('Request timed out')
      throw new Error('Request timed out. Please try again.')
    }
    console.error('Error sending chat message:', error)
    if (error instanceof Error) {
      console.error('Error details:', error.message, error.stack)
    }
    throw error
  }
}

