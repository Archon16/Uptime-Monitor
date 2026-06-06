import { useEffect, useState } from 'react'
import { fetchURLs, addURL, deleteURL } from './api'
import UrlForm from './components/UrlForm'
import UrlTable from './components/UrlTable'

function App() {
  const [urls, setUrls] = useState([])

  const load = async () => {
    try {
      const data = await fetchURLs()
      setUrls(data)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleAdd = async (url, name) => {
    await addURL(url, name)
    load()
  }

  const handleDelete = async (id) => {
    await deleteURL(id)
    load()
  }

  return (
    <div className="container">
      <h1>Uptime Monitor</h1>
      <p className="meta">Monitoring {urls.length} URL{urls.length !== 1 ? 's' : ''}</p>
      <UrlForm onAdd={handleAdd} />
      <UrlTable urls={urls} onDelete={handleDelete} />
    </div>
  )
}

export default App
