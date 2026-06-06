import StatusBadge from './StatusBadge'

function UrlTable({ urls, onDelete }) {
  if (urls.length === 0) {
    return <p>No URLs being monitored yet.</p>
  }

  const fmtDate = (d) => {
    if (!d) return '-'
    return new Date(d).toLocaleString()
  }

  return (
    <table>
      <thead>
        <tr>
          <th>URL</th>
          <th>Name</th>
          <th>Status</th>
          <th>Response Time</th>
          <th>Last Checked</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {urls.map((u) => (
          <tr key={u.id}>
            <td>{u.url}</td>
            <td>{u.name || '-'}</td>
            <td><StatusBadge isUp={u.is_up} /></td>
            <td>{u.response_time_ms != null ? `${u.response_time_ms}ms` : '-'}</td>
            <td>{fmtDate(u.last_checked_at)}</td>
            <td>
              <button className="delete-btn" onClick={() => onDelete(u.id)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default UrlTable
