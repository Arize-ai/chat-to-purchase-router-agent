export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}

export function formatRating(rating: number): string {
  return rating.toFixed(1)
}

export function getImagePath(imagePath: string): string {
  return `/${imagePath}`
}

export function truncateText(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

