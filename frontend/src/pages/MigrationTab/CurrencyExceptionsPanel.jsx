function formatAmount(value) {
  if (value === null || value === undefined) return "—";
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * CurrencyExceptionsPanel
 *
 * Shows the rows a /process (or delete-mismatches) response flagged under
 * `currency_mismatches` -- rows whose ECC company code carries a currency
 * other than the one it's required to use.
 *
 * Under the updated policy these rows are NOT removed from ECC
 * automatically and do NOT block processing. The panel is now
 * informational: review the flagged rows and, only if you want to, remove
 * them from the batch.
 *
 * Props:
 *  - mismatches: array of { record, document, company_code, customer,
 *                currency, expected_currency, amount }
 *  - onDeleteAndProcess: async () => void
 *  - deleting: boolean
 *  - deletedRowsAvailable: boolean
 *  - onDownloadDeletedRows: async () => void
 *  - downloadingDeletedRows: boolean
 */
function CurrencyExceptionsPanel({
  mismatches,
  onDeleteAndProcess,
  deleting,
  deletedRowsAvailable,
  onDownloadDeletedRows,
  downloadingDeletedRows,
}) {
  const hasMismatches = mismatches && mismatches.length > 0;

  if (!hasMismatches && !deletedRowsAvailable) return null;

  const downloadButton = deletedRowsAvailable && (
    <button
      onClick={onDownloadDeletedRows}
      disabled={downloadingDeletedRows}
      className="px-5 py-2.5 border border-red-700 text-red-700 rounded-lg disabled:opacity-60 hover:bg-red-100 transition-colors"
    >
      {downloadingDeletedRows ? "Preparing file..." : "Download Deleted Rows"}
    </button>
  );

  if (!hasMismatches) {
    return (
      <div className="flex flex-col gap-3 border border-red-200 bg-red-50 rounded-lg p-4 w-full">
        <div>
          <h2 className="text-sm font-semibold text-red-800">
            Currency Exceptions
          </h2>
          <p className="text-xs text-red-700 mt-0.5">
            No open exceptions. Rows removed earlier this session are still
            available below.
          </p>
        </div>
        <div>{downloadButton}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 border border-red-300 bg-red-50 rounded-lg p-4 w-full">
      <div>
        <h2 className="text-sm font-semibold text-red-800">
          Currency Exceptions
        </h2>
        <p className="text-xs text-red-700 mt-0.5">
          {mismatches.length} row{mismatches.length === 1 ? "" : "s"} carr
          {mismatches.length === 1 ? "ies" : "y"} a currency that doesn't
          match its company code's expected currency. These rows are included
          in the S/4 workbook and have NOT been removed from ECC — you can
          keep them, or remove them below if you want them excluded.
        </p>
      </div>

      <div className="border border-red-200 rounded-lg overflow-auto max-h-[40vh] bg-white">
        <table className="min-w-full text-xs">
          <thead className="sticky top-0 bg-red-700 text-white">
            <tr>
              <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Row</th>
              <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Document</th>
              <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Company Code</th>
              <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Customer</th>
              <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Currency</th>
              <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Expected</th>
              <th className="px-3 py-2 text-right font-medium whitespace-nowrap">Amount</th>
            </tr>
          </thead>
          <tbody>
            {mismatches.map((m, i) => (
              <tr
                key={m.record ?? i}
                className={i % 2 === 0 ? "bg-white" : "bg-red-50"}
              >
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100 font-mono">
                  {m.record}
                </td>
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100 font-mono">
                  {m.document || "—"}
                </td>
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100">
                  {m.company_code}
                </td>
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100 font-mono">
                  {m.customer || "—"}
                </td>
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100 font-medium text-red-700">
                  {m.currency}
                </td>
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100 text-gray-500">
                  {m.expected_currency}
                </td>
                <td className="px-3 py-2 whitespace-nowrap border-t border-red-100 text-right font-mono">
                  {formatAmount(m.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          onClick={onDeleteAndProcess}
          disabled={deleting}
          className="px-5 py-2.5 bg-red-700 text-white rounded-lg disabled:opacity-60 hover:bg-red-800 transition-colors"
        >
          {deleting ? "Removing & reprocessing..." : "Remove & Reprocess"}
        </button>
        {downloadButton}
      </div>
      <p className="text-xs text-red-700">
        Removes these rows from the staged ECC file and reprocesses without
        them. Optional — this cannot be undone, so re-fetch from ECC if you
        change your mind.
      </p>
    </div>
  );
}

export default CurrencyExceptionsPanel;