// import { useEffect, useState } from "react";
// import { getLatestFiles, validateAR, loadToS4 } from "../../api/client";

// function StatusPill({ status }) {
//   const color =
//     status === "PASS"
//       ? "bg-emerald-100 text-emerald-700"
//       : status === "FAIL"
//       ? "bg-red-100 text-red-700"
//       : "bg-amber-100 text-amber-700";
//   return (
//     <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
//       {status}
//     </span>
//   );
// }

// function FileCard({ label, file }) {
//   return (
//     <div className="flex-1 border border-gray-200 rounded-lg p-4">
//       <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
//       {file ? (
//         <>
//           <p className="font-mono text-sm text-[#0B1F3A] break-all">{file.name}</p>
//           <p className="text-xs text-gray-500 mt-1">
//             {file.size.toLocaleString()} bytes · {file.modified}
//           </p>
//         </>
//       ) : (
//         <p className="text-sm text-amber-600">Not staged yet.</p>
//       )}
//     </div>
//   );
// }

// function CheckRow({ check }) {
//   return (
//     <div className="border border-gray-200 rounded-lg p-4">
//       <div className="flex items-center justify-between">
//         <p className="font-medium text-[#0B1F3A]">{check.check_name}</p>
//         <StatusPill status={check.status} />
//       </div>
//       <p className="text-xs text-gray-600 mt-1">{check.message}</p>

//       {check.details?.length > 0 && (
//         <table className="mt-3 w-full text-xs">
//           <thead className="text-gray-500">
//             <tr>
//               <th className="text-left py-1">Label</th>
//               <th className="text-right py-1">ECC</th>
//               <th className="text-right py-1">S/4</th>
//               <th className="text-left py-1 pl-3">Status</th>
//             </tr>
//           </thead>
//           <tbody>
//             {check.details.map((d, i) => (
//               <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
//                 <td className="py-1">{d.label}</td>
//                 <td className="py-1 text-right font-mono">
//                   {d.left_count == null
//                     ? "—"
//                     : d.money
//                     ? d.left_count.toFixed(2)
//                     : d.left_count.toLocaleString()}
//                 </td>
//                 <td className="py-1 text-right font-mono">
//                   {d.right_count == null
//                     ? "—"
//                     : d.money
//                     ? d.right_count.toFixed(2)
//                     : d.right_count.toLocaleString()}
//                 </td>
//                 <td className="py-1 pl-3">
//                   <StatusPill status={d.status} />
//                 </td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       )}
//     </div>
//   );
// }

// function ValidatePage() {
//   const [files, setFiles] = useState({ ecc: null, s4: null });
//   const [filesLoading, setFilesLoading] = useState(true);
//   const [filesError, setFilesError] = useState(null);

//   const [validating, setValidating] = useState(false);
//   const [report, setReport] = useState(null);
//   const [validateError, setValidateError] = useState(null);

//   const [loading, setLoading] = useState(false);
//   const [loadResult, setLoadResult] = useState(null);
//   const [loadError, setLoadError] = useState(null);

//   // Step 3 — auto-load latest staged files on mount.
//   useEffect(() => {
//     setFilesLoading(true);
//     getLatestFiles()
//       .then(setFiles)
//       .catch((e) => setFilesError(e.message))
//       .finally(() => setFilesLoading(false));
//   }, []);

//   const ready = Boolean(files.ecc && files.s4);
//   const pass = report?.overall_status === "PASS";

//   const onValidate = async () => {
//     setValidating(true);
//     setValidateError(null);
//     setReport(null);
//     setLoadResult(null);
//     try {
//       const r = await validateAR();
//       setReport(r);
//     } catch (e) {
//       setValidateError(e.message);
//     } finally {
//       setValidating(false);
//     }
//   };

//   const onLoad = async () => {
//     setLoading(true);
//     setLoadError(null);
//     setLoadResult(null);
//     try {
//       const r = await loadToS4();
//       setLoadResult(r);
//     } catch (e) {
//       setLoadError(e.message);
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-6">
//       <div>
//         <h1 className="text-xl font-semibold text-[#0B1F3A]">Validate & Load</h1>
//         <p className="text-sm text-gray-500">
//           Compare staged ECC and S/4 data, then push the cleaned rows into S/4.
//         </p>
//       </div>

//       {/* --- File preview --- */}
//       <div className="flex gap-4">
//         <FileCard label="ECC staging" file={filesLoading ? null : files.ecc} />
//         <FileCard label="S/4 staging" file={filesLoading ? null : files.s4} />
//       </div>

//       {filesError && <p className="text-xs text-red-600">{filesError}</p>}
//       {!filesLoading && !ready && !filesError && (
//         <p className="text-sm text-amber-600">
//           Both files must be staged. Run Fetch and Process first.
//         </p>
//       )}

//       {/* --- Validate --- */}
//       <div className="flex flex-col items-start gap-2">
//         <button
//           onClick={onValidate}
//           disabled={!ready || validating}
//           className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
//         >
//           {validating ? "Validating..." : "Validate"}
//         </button>
//         {validateError && <p className="text-xs text-red-600">{validateError}</p>}
//       </div>

//       {/* --- Report --- */}
//       {report && (
//         <div className="flex flex-col gap-3">
//           <div className="flex items-center gap-3">
//             <p className="text-sm text-gray-700">
//               Overall: <StatusPill status={report.overall_status} />
//             </p>
//             <p className="text-xs text-gray-500">
//               {report.summary.passed} / {report.summary.total_checks} checks passed
//             </p>
//           </div>
//           {report.checks.map((c) => (
//             <CheckRow key={c.check_name} check={c} />
//           ))}
//         </div>
//       )}

//       {/* --- Load to S/4 --- */}
//       {report && (
//         <div className="flex flex-col items-start gap-2 border-t border-gray-200 pt-5">
//           <button
//             onClick={onLoad}
//             disabled={!pass || loading}
//             className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
//             title={!pass ? "Validation must pass before loading" : undefined}
//           >
//             {loading ? "Loading into S/4..." : "Load into S/4"}
//           </button>
//           {!pass && (
//             <p className="text-xs text-amber-600">
//               Load is disabled until validation passes.
//             </p>
//           )}
//           {loadError && <p className="text-xs text-red-600">{loadError}</p>}
//           {loadResult && (
//             <p className="text-xs text-emerald-600">
//               {loadResult.status} — {loadResult.success_count} succeeded,{" "}
//               {loadResult.error_count} failed.
//             </p>
//           )}
//         </div>
//       )}
//     </div>
//   );
// }

// export default ValidatePage;

import { useEffect, useState } from "react";
import {
  getLatestFiles,
  validateAR,
  loadToS4,
  downloadValidationReport,
} from "../../api/client";

function StatusPill({ status }) {
  const color =
    status === "PASS"
      ? "bg-emerald-100 text-emerald-700"
      : status === "FAIL"
      ? "bg-red-100 text-red-700"
      : "bg-amber-100 text-amber-700";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}

function FileCard({ label, file }) {
  return (
    <div className="flex-1 border border-gray-200 rounded-lg p-4">
      <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
      {file ? (
        <>
          <p className="font-mono text-sm text-[#0B1F3A] break-all">{file.name}</p>
          <p className="text-xs text-gray-500 mt-1">
            {file.size.toLocaleString()} bytes · {file.modified}
          </p>
        </>
      ) : (
        <p className="text-sm text-amber-600">Not staged yet.</p>
      )}
    </div>
  );
}

function CheckRow({ check }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <p className="font-medium text-[#0B1F3A]">{check.check_name}</p>
        <StatusPill status={check.status} />
      </div>
      <p className="text-xs text-gray-600 mt-1">{check.message}</p>

      {check.details?.length > 0 && (
        <table className="mt-3 w-full text-xs">
          <thead className="text-gray-500">
            <tr>
              <th className="text-left py-1">Label</th>
              <th className="text-right py-1">ECC</th>
              <th className="text-right py-1">S/4</th>
              <th className="text-left py-1 pl-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {check.details.map((d, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="py-1">{d.label}</td>
                <td className="py-1 text-right font-mono">
                  {d.left_count == null
                    ? "—"
                    : d.money
                    ? d.left_count.toFixed(2)
                    : d.left_count.toLocaleString()}
                </td>
                <td className="py-1 text-right font-mono">
                  {d.right_count == null
                    ? "—"
                    : d.money
                    ? d.right_count.toFixed(2)
                    : d.right_count.toLocaleString()}
                </td>
                <td className="py-1 pl-3">
                  <StatusPill status={d.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function ValidatePage() {
  const [files, setFiles] = useState({ ecc: null, s4: null });
  const [filesLoading, setFilesLoading] = useState(true);
  const [filesError, setFilesError] = useState(null);

  const [validating, setValidating] = useState(false);
  const [report, setReport] = useState(null);
  const [validateError, setValidateError] = useState(null);

  const [loading, setLoading] = useState(false);
  const [loadResult, setLoadResult] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  // Step 3 — auto-load latest staged files on mount.
  useEffect(() => {
    setFilesLoading(true);
    getLatestFiles()
      .then(setFiles)
      .catch((e) => setFilesError(e.message))
      .finally(() => setFilesLoading(false));
  }, []);

  const ready = Boolean(files.ecc && files.s4);
  const pass = report?.overall_status === "PASS";

  const onValidate = async () => {
    setValidating(true);
    setValidateError(null);
    setReport(null);
    setLoadResult(null);
    try {
      const r = await validateAR();
      setReport(r);
    } catch (e) {
      setValidateError(e.message);
    } finally {
      setValidating(false);
    }
  };

  const onDownloadReport = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const blob = await downloadValidationReport();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "AR_Validation_Report.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setDownloadError(e.message);
    } finally {
      setDownloading(false);
    }
  };

  const onLoad = async () => {
    setLoading(true);
    setLoadError(null);
    setLoadResult(null);
    try {
      const r = await loadToS4();
      setLoadResult(r);
    } catch (e) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-[#0B1F3A]">Validate & Load</h1>
        <p className="text-sm text-gray-500">
          Compare staged ECC and S/4 data, then push the cleaned rows into S/4.
        </p>
      </div>

      {/* --- File preview --- */}
      <div className="flex gap-4">
        <FileCard label="ECC staging" file={filesLoading ? null : files.ecc} />
        <FileCard label="S/4 staging" file={filesLoading ? null : files.s4} />
      </div>

      {filesError && <p className="text-xs text-red-600">{filesError}</p>}
      {!filesLoading && !ready && !filesError && (
        <p className="text-sm text-amber-600">
          Both files must be staged. Run Fetch and Process first.
        </p>
      )}

      {/* --- Validate --- */}
      <div className="flex flex-col items-start gap-2">
        <button
          onClick={onValidate}
          disabled={!ready || validating}
          className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
        >
          {validating ? "Validating..." : "Validate"}
        </button>
        {validateError && <p className="text-xs text-red-600">{validateError}</p>}
      </div>

      {/* --- Report --- */}
      {report && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <p className="text-sm text-gray-700">
              Overall: <StatusPill status={report.overall_status} />
            </p>
            <p className="text-xs text-gray-500">
              {report.summary.passed} / {report.summary.total_checks} checks passed
            </p>
          </div>
          {report.checks.map((c) => (
            <CheckRow key={c.check_name} check={c} />
          ))}
        </div>
      )}

      {/* --- Load to S/4 --- */}
      {report && (
        <div className="flex flex-col items-start gap-2 border-t border-gray-200 pt-5">
          <div className="flex gap-3">
            <button
              onClick={onLoad}
              disabled={!pass || loading}
              className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
              title={!pass ? "Validation must pass before loading" : undefined}
            >
              {loading ? "Loading into S/4..." : "Load into S/4"}
            </button>
            <button
              onClick={onDownloadReport}
              disabled={downloading}
              className="px-5 py-2.5 border border-[#0B1F3A] text-[#0B1F3A] rounded-lg disabled:opacity-60"
            >
              {downloading ? "Preparing report..." : "Download Validation Report"}
            </button>
          </div>
          {!pass && (
            <p className="text-xs text-amber-600">
              Load is disabled until validation passes.
            </p>
          )}
          {loadError && <p className="text-xs text-red-600">{loadError}</p>}
          {loadResult && (
            <p className="text-xs text-emerald-600">
              {loadResult.status} — {loadResult.success_count} succeeded,{" "}
              {loadResult.error_count} failed.
            </p>
          )}
          {downloadError && <p className="text-xs text-red-600">{downloadError}</p>}
        </div>
      )}
    </div>
  );
}

export default ValidatePage;