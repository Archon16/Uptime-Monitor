function StatusBadge({ isUp }) {
  if (isUp === true) {
    return <span className="status-up">UP</span>
  }
  if (isUp === false) {
    return <span className="status-down">DOWN</span>
  }
  return <span>-</span>
}

export default StatusBadge
