import { useState } from 'react'

function UrlForm({ onAdd }) {
  const [url, setUrl] = useState('')
  const [name, setName] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!url.trim()) return
    onAdd(url.trim(), name.trim() || undefined)
    setUrl('')
    setName('')
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="url"
        placeholder="https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        required
      />
      <input
        type="text"
        placeholder="Name (optional)"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button type="submit">Add URL</button>
    </form>
  )
}

export default UrlForm
