function DataTable({ columns, rows, resultColumnIndex }) {
    return (
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
  
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => {
                  const isResult = cellIndex === resultColumnIndex;
  
                  return (
                    <td key={cellIndex}>
                      {isResult ? (
                        <span
                          className={`result-badge ${
                            cell === "Non-Compliant" ? "danger" : "ok"
                          }`}
                        >
                          <span className="result-dot"></span>
                          {cell}
                        </span>
                      ) : (
                        cell
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  
  export default DataTable;