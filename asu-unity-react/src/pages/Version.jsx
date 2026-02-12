export default function Version() {
  return (
    <div className="container py-5">
      <h1 className="display-6 fw-bold mb-4">Version</h1>
      <div className="border rounded p-4 bg-white">
        <table className="table table-borderless mb-0">
          <tbody>
            <tr>
              <th className="text-muted" style={{ width: "150px" }}>Commit</th>
              <td><code>{__COMMIT_HASH__}</code></td>
            </tr>
            <tr>
              <th className="text-muted">Message</th>
              <td>{__COMMIT_MESSAGE__}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
