import { Pool } from 'pg'
import Header from './components/Header'
import ProductList from './components/ProductList'
import { Product } from './types'

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'chat_to_purchase',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
})

async function getProducts() {
  const client = await pool.connect()
  try {
    const result = await client.query('SELECT * FROM products ORDER BY id')
    return result.rows.map((p: any) => ({
      ...p,
      price: Number(p.price),
      rating: Number(p.rating),
    }))
  } finally {
    client.release()
  }
}

export default async function Home() {
  try {
    const products = await getProducts()

    return (
      <div className="container">
        <Header title="Shoe Catalog" />
        <ProductList products={products as Product[]} />
      </div>
    )
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : 'Unknown error occurred'
    return (
      <div className="container">
        <div className="error">
          <h2>Error loading products</h2>
          <p>{errorMessage}</p>
          <p style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
            Make sure your database is running: <code>docker-compose up -d</code>
          </p>
        </div>
      </div>
    )
  }
}

