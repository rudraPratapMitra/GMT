// import { useEffect, useState } from "react";
// import { processARData } from "../../api/client";

// const Process_func = {
//   ar: processARData,
// };

// function ProcessButton({ hasData, process = "ar" }) {
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState(null);
//   const [result, setResult] = useState(null);

//   // A new fetch invalidates the previous run's message.
//   useEffect(() => {
//     setResult(null);
//     setError(null);
//   }, [hasData]);

//   const handleClick = async () => {
//     const processFn = Process_func[process];
//     if (!processFn) {
//       setError(`No processing wired up yet for "${process}"`);
//       return;
//     }

//     setLoading(true);
//     setError(null);
//     setResult(null);
//     try {
//       // No arguments — backend reads the staged ECC file from disk.
//       const response = await processFn();
//       setResult(response);
//     } catch (err) {
//       setError(err.message);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="flex flex-col items-start gap-2">
//       <button
//         onClick={handleClick}
//         disabled={!hasData || loading}
//         className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
//       >
//         {loading ? "Processing..." : "Process"}
//       </button>

//       {!hasData && <p className="text-xs text-gray-400">Fetch data first.</p>}

//       {result && result.warning_count === 0 && (
//         <p className="text-xs text-emerald-600">
//           Transformed {result.row_count} row{result.row_count === 1 ? "" : "s"} with no
//           warnings. Staged as <span className="font-mono">{result.file}</span>.
//           Ready to validate.
//         </p>
//       )}
//       {result && result.warning_count > 0 && (
//         <p className="text-xs text-amber-600">
//           Transformed {result.row_count} row{result.row_count === 1 ? "" : "s"} with{" "}
//           {result.warning_count} warning{result.warning_count === 1 ? "" : "s"}. See the
//           &quot;Warnings&quot; sheet in <span className="font-mono">{result.file}</span>.
//           Load-to-S/4 will be blocked until these are resolved.
//         </p>
//       )}
//       {error && <p className="text-xs text-red-600">{error}</p>}
//     </div>
//   );
// }

// export default ProcessButton;

import { useEffect, useState } from "react";
import { processARData, deleteMismatchesAndProcess } from "../../api/client";
import CurrencyExceptionsPanel from "./CurrencyExceptionsPanel";

const Process_func = {
  ar: processARData,
};

function ProcessButton({ hasData, process = "ar" }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // A new fetch invalidates the previous run's message.
  useEffect(() => {
    setResult(null);
    setError(null);
  }, [hasData]);

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
      // No arguments — backend reads the staged ECC file from disk.
      const response = await processFn();
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAndProcess = async () => {
    if (!result?.currency_mismatches?.length) return;
    setDeleting(true);
    setError(null);
    try {
      const recordIndices = result.currency_mismatches.map((m) => m.record);
      const response = await deleteMismatchesAndProcess(recordIndices);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <button
        onClick={handleClick}
        disabled={!hasData || loading}
        className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
      >
        {loading ? "Processing..." : "Process"}
      </button>

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
          {result.warning_count} warning{result.warning_count === 1 ? "" : "s"}. See the
          &quot;Warnings&quot; sheet in <span className="font-mono">{result.file}</span>.
          Load-to-S/4 will be blocked until these are resolved.
        </p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}

      <CurrencyExceptionsPanel
        mismatches={result?.currency_mismatches}
        onDeleteAndProcess={handleDeleteAndProcess}
        deleting={deleting}
      />
    </div>
  );
}

export default ProcessButton;