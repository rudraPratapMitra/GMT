import { useEffect, useRef, useState } from "react";
import {
  processARData,
  deleteMismatchesAndProcess,
  downloadDeletedRows,
  downloadWarningRows,
  downloadS4Workbook,
} from "../../api/client";
import CurrencyExceptionsPanel from "./CurrencyExceptionsPanel";

const Process_func = {
  ar: processARData,
};

function triggerBlobDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

function ProcessButton({ hasData, process = "ar" }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [downloadingDeletedRows, setDownloadingDeletedRows] = useState(false);
  const [downloadingWarningRows, setDownloadingWarningRows] = useState(false);
  const [downloadingS4, setDownloadingS4] = useState(false);

  // Guards against the auto-download firing twice (StrictMode re-mount,
  // or two process responses landing in the same tick).
  const lastAutoDownloadedFile = useRef(null);

  // A new fetch invalidates the previous run's message.
  useEffect(() => {
    setResult(null);
    setError(null);
    lastAutoDownloadedFile.current = null;
  }, [hasData]);

  // Auto-download the S4 workbook as soon as a fresh /process response
  // arrives. Re-download is still available via the button below.
  useEffect(() => {
    if (!result?.file) return;
    if (lastAutoDownloadedFile.current === result.file) return;
    lastAutoDownloadedFile.current = result.file;

    (async () => {
      try {
        const blob = await downloadS4Workbook();
        triggerBlobDownload(blob, result.file);
      } catch (err) {
        // Non-fatal: the button below is the fallback.
        setError(`Auto-download failed: ${err.message}`);
      }
    })();
  }, [result?.file]);

  const handleClick = async () => {
    const processFn = Process_func[process];
    if (!processFn) {
      setError(`No processing wired up yet for "${process}"`);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await processFn();
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadS4 = async () => {
    setDownloadingS4(true);
    setError(null);
    try {
      const blob = await downloadS4Workbook();
      triggerBlobDownload(blob, result?.file || "AR_S4_Load.xlsx");
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloadingS4(false);
    }
  };

  const handleDownloadWarningRows = async () => {
    setDownloadingWarningRows(true);
    setError(null);
    try {
      const blob = await downloadWarningRows();
      triggerBlobDownload(blob, "Warning_Rows.xlsx");
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloadingWarningRows(false);
    }
  };

  const handleDownloadDeletedRows = async () => {
    setDownloadingDeletedRows(true);
    setError(null);
    try {
      const blob = await downloadDeletedRows();
      triggerBlobDownload(blob, "Deleted_ECC_Rows.xlsx");
    } catch (err) {
      setError(err.message);
    } finally {
      setDownloadingDeletedRows(false);
    }
  };

  const handleDeleteAndProcess = async () => {
    if (!result?.currency_mismatches?.length) return;
    setDeleting(true);
    setError(null);
    try {
      const recordIndices = result.currency_mismatches.map((m) => m.record);
      const response = await deleteMismatchesAndProcess(recordIndices);
      // Force a re-auto-download for the new file name.
      lastAutoDownloadedFile.current = null;
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-3">
      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleClick}
          disabled={!hasData || loading}
          className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
        >
          {loading ? "Processing..." : "Process"}
        </button>

        {result && (
          <button
            onClick={handleDownloadS4}
            disabled={downloadingS4}
            className="px-5 py-2.5 border border-[#0B1F3A] text-[#0B1F3A] rounded-lg disabled:opacity-60 hover:bg-gray-50 transition-colors"
          >
            {downloadingS4 ? "Preparing workbook..." : "Download S/4 Workbook"}
          </button>
        )}

        {result?.warning_rows_available && (
          <button
            onClick={handleDownloadWarningRows}
            disabled={downloadingWarningRows}
            className="px-5 py-2.5 border border-amber-500 text-amber-700 rounded-lg disabled:opacity-60 hover:bg-amber-50 transition-colors"
          >
            {downloadingWarningRows
              ? "Preparing file..."
              : "Download Warning Rows"}
          </button>
        )}
      </div>

      {!hasData && <p className="text-xs text-gray-400">Fetch data first.</p>}

      {result && result.warning_count === 0 && (
        <p className="text-xs text-emerald-600">
          Transformed {result.row_count} row{result.row_count === 1 ? "" : "s"} with no
          warnings. Staged as <span className="font-mono">{result.file}</span>.
          Ready to validate.
        </p>
      )}

      {result && result.warning_count > 0 && (
        <p className="text-xs text-amber-600">
          Transformed {result.row_count} row{result.row_count === 1 ? "" : "s"} with{" "}
          {result.warning_count} warning{result.warning_count === 1 ? "" : "s"}. The full
          S/4 workbook is still available — download it to review flagged rows (also
          available as a separate Warning Rows Excel). Nothing has been removed from ECC.
        </p>
      )}

      {error && <p className="text-xs text-red-600">{error}</p>}

      <CurrencyExceptionsPanel
        mismatches={result?.currency_mismatches}
        onDeleteAndProcess={handleDeleteAndProcess}
        deleting={deleting}
        deletedRowsAvailable={Boolean(result?.deleted_rows_available)}
        onDownloadDeletedRows={handleDownloadDeletedRows}
        downloadingDeletedRows={downloadingDeletedRows}
      />
    </div>
  );
}

export default ProcessButton;