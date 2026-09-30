// import { useEffect, useState } from "react";
// import {
//   getLatestFiles,
//   validateAR,
//   downloadValidationReport,
//   downloadS4Workbook,
//   downloadValidationExcel,
// } from "../../api/client";

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

//   const [downloadingReport, setDownloadingReport] = useState(false);
//   const [downloadingS4, setDownloadingS4] = useState(false);
//   const [downloadError, setDownloadError] = useState(null);

//   useEffect(() => {
//     setFilesLoading(true);
//     getLatestFiles()
//       .then(setFiles)
//       .catch((e) => setFilesError(e.message))
//       .finally(() => setFilesLoading(false));
//   }, []);

//   const ready = Boolean(files.ecc && files.s4);

//   const onValidate = async () => {
//     setValidating(true);
//     setValidateError(null);
//     setReport(null);
//     try {
//       const r = await validateAR();
//       setReport(r);
//     } catch (e) {
//       setValidateError(e.message);
//     } finally {
//       setValidating(false);
//     }
//   };

//   const saveBlob = (blob, filename) => {
//     const url = window.URL.createObjectURL(blob);
//     const a = document.createElement("a");
//     a.href = url;
//     a.download = filename;
//     document.body.appendChild(a);
//     a.click();
//     a.remove();
//     window.URL.revokeObjectURL(url);
//   };

//   // One click downloads both files: the PDF report and the validation Excel.
//   const onDownloadReport = async () => {
//     setDownloadingReport(true);
//     setDownloadError(null);
//     try {
//       // Fetch both first so a failure in either one downloads nothing.
//       const [pdf, xlsx] = await Promise.all([
//         downloadValidationReport(),
//         downloadValidationExcel(),
//       ]);
//       saveBlob(pdf, "AR_Validation_Report.pdf");
//       setTimeout(() => saveBlob(xlsx, "AR_Validation_Data.xlsx"), 400);
//     } catch (e) {
//       setDownloadError(e.message);
//     } finally {
//       setDownloadingReport(false);
//     }
//   };

//   const onDownloadS4 = async () => {
//     setDownloadingS4(true);
//     setDownloadError(null);
//     try {
//       const blob = await downloadS4Workbook();
//       saveBlob(blob, files.s4?.name || "AR_S4_Load.xlsx");
//     } catch (e) {
//       setDownloadError(e.message);
//     } finally {
//       setDownloadingS4(false);
//     }
//   };

//   return (
//     <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-6">
//       <div>
//         <h1 className="text-xl font-semibold text-[#0B1F3A]">Validate</h1>
//         <p className="text-sm text-gray-500">
//           Compare staged ECC and S/4 data, then download the S/4 LTMC workbook
//           for the standard S/4 import process.
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

//       {/* --- Downloads --- */}
//       {report && (
//         <div className="flex flex-col items-start gap-2 border-t border-gray-200 pt-5">
//           <div className="flex flex-wrap gap-3">
//             <button
//               onClick={onDownloadS4}
//               disabled={downloadingS4}
//               className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
//             >
//               {downloadingS4 ? "Preparing workbook..." : "Download S/4 Workbook"}
//             </button>
//             <button
//               onClick={onDownloadReport}
//               disabled={downloadingReport}
//               className="px-5 py-2.5 border border-[#0B1F3A] text-[#0B1F3A] rounded-lg disabled:opacity-60"
//             >
//               {downloadingReport
//                 ? "Preparing report..."
//                 : "Download Validation Report + Excel"}
//             </button>
//           </div>
//           {downloadError && <p className="text-xs text-red-600">{downloadError}</p>}
//           <p className="text-xs text-gray-500">
//             Direct S/4 loading is disabled. Use the S/4 workbook with the
//             standard S/4 import process. The validation report downloads as a
//             PDF plus an Excel file with the ECC source values next to each
//             mapped S/4 column.
//           </p>
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
  downloadValidationReport,
  downloadValidationExcel,
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

  const [downloadingReport, setDownloadingReport] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  useEffect(() => {
    setFilesLoading(true);
    getLatestFiles()
      .then(setFiles)
      .catch((e) => setFilesError(e.message))
      .finally(() => setFilesLoading(false));
  }, []);

  const ready = Boolean(files.ecc && files.s4);

  const onValidate = async () => {
    setValidating(true);
    setValidateError(null);
    setReport(null);
    try {
      const r = await validateAR();
      setReport(r);
    } catch (e) {
      setValidateError(e.message);
    } finally {
      setValidating(false);
    }
  };

  const saveBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  // One click downloads both files: the PDF report and the validation Excel.
  const onDownloadReport = async () => {
    setDownloadingReport(true);
    setDownloadError(null);
    try {
      // Fetch both first so a failure in either one downloads nothing.
      const [pdf, xlsx] = await Promise.all([
        downloadValidationReport(),
        downloadValidationExcel(),
      ]);
      saveBlob(pdf, "AR_Validation_Report.pdf");
      setTimeout(() => saveBlob(xlsx, "AR_Validation_Data.xlsx"), 400);
    } catch (e) {
      setDownloadError(e.message);
    } finally {
      setDownloadingReport(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-[#0B1F3A]">Validate</h1>
        <p className="text-sm text-gray-500">
          Compare staged ECC and S/4 data, then download the validation report
          and Excel.
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

      {/* --- Downloads --- */}
      {report && (
        <div className="flex flex-col items-start gap-2 border-t border-gray-200 pt-5">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={onDownloadReport}
              disabled={downloadingReport}
              className="px-5 py-2.5 border border-[#0B1F3A] text-[#0B1F3A] rounded-lg disabled:opacity-60"
            >
              {downloadingReport
                ? "Preparing report..."
                : "Download Validation Report + Excel"}
            </button>
          </div>
          {downloadError && <p className="text-xs text-red-600">{downloadError}</p>}
          <p className="text-xs text-gray-500">
            Direct S/4 loading is disabled. The validation report downloads as a
            PDF plus an Excel file with the ECC source values next to each
            mapped S/4 column.
          </p>
        </div>
      )}
    </div>
  );
}

export default ValidatePage;