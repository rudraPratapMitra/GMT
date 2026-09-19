// Raw SAP OData dates look like "/Date(1762473600000)/" -- render them
// as plain dates instead of the raw string when we spot the pattern.
function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string") {
    const match = value.match(/\/Date\((\d+)(?:[+-]\d+)?\)\//);
    if (match) {
      return new Date(Number(match[1])).toLocaleDateString();
    }
  }
  return String(value);
}

/**
 * DataPreview
 *
 * Props:
 *  - data:    array of row objects, e.g. what fetchARData() resolves with.
 *             Columns are derived from the first row's keys, so this works
 *             whether rows use raw SAP field codes (BUKRS, BELNR...) or
 *             friendly names (Company Code, Document Number...) -- it
 *             doesn't need to know which.
 *  - loading: boolean, shows a loading state instead of the table/empty state
 */
const PREVIEW_LIMIT = 50;

function DataPreview({ data, loading }) {
  if (loading) {
    return (
      <div className="border border-gray-200 rounded-lg p-6 text-sm text-gray-500">
        Loading data…
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="border border-gray-200 rounded-lg p-6 text-sm text-gray-500">
        No data fetched yet. Click "Fetch Data" to pull records.
      </div>
    );
  }

  // __metadata is SAP OData noise, not real field data -- never show it.
  const columns = Object.keys(data[0]).filter((key) => key !== "__metadata");
  const visibleRows = data.slice(0, PREVIEW_LIMIT);
  const isSampled = data.length > PREVIEW_LIMIT;

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs text-gray-500">
        {isSampled
          ? `Showing first ${PREVIEW_LIMIT} of ${data.length} rows · ${columns.length} columns`
          : `${data.length} row${data.length === 1 ? "" : "s"} · ${columns.length} columns`}
      </p>
      <div className="border border-gray-200 rounded-lg overflow-auto max-h-[70vh]">
        <table className="min-w-full text-xs">
          <thead className="sticky top-0 bg-[#0B1F3A] text-white">
            <tr>
              {columns.map((col) => (
                <th key={col} className="px-3 py-2 text-left whitespace-nowrap font-medium">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((row, i) => (
              <tr
                key={i}
                className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}
              >
                {columns.map((col) => (
                  <td key={col} className="px-3 py-2 whitespace-nowrap border-t border-gray-100">
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {isSampled && (
        <p className="text-xs text-gray-400">
          Note: all {data.length} fetched rows are still in memory and will be used for processing, only the preview is limited.
        </p>
      )}
    </div>
  );
}

export default DataPreview;