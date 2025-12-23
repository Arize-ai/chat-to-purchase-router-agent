import './globals.css'
import { CartProvider } from './cart/CartContext'

export const metadata = {
  title: 'Product Catalog',
  description: 'Browse our product catalog',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <CartProvider>{children}</CartProvider>
      </body>
    </html>
  )
}

