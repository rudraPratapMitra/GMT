// import {useState} from "react"
// function ProcessButton({data,onProcessed}){
//     const[loading,setLoading]=useState(false)
//     const[error,setError]=useState(null)

//     const hasData=Array.isArray(data)&&data.length>0
//     const handleClick=async()=>{
//         setLoading(true);
//         setError(null)
//         try {
//             await new Promise((resolve) => {
//                 setTimeout(()=>{
//                     resolve();
//                 },500);
//             });
//         } catch (error) {
//             setError(error.message)
//         }finally{
//             setLoading(false)
//         }
//     }
//     return(
//         <div>
//             <button 
//                 onClick={handleClick}
//                 disabled={!hasData || loading}
//                 className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60">
//                     {loading?"Processing...":"Process"}
//             </button> 
//             {!hasData && (
//         <p className="text-xs text-gray-400">Fetch data first.</p>
//       )}
//       {error && <p className="text-xs text-red-600">{error}</p>}
//     </div>
//     )
// }
// export default ProcessButton

import { useEffect, useState } from "react";
import { processARData } from "../../api/client";

const Process_func = {
  ar: processARData,
};

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function ProcessButton({ data, process = "ar" }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const hasData = Array.isArray(data) && data.length > 0;

  // A new fetch replaces the data, so the previous run's message is stale.
  useEffect(() => {
    setResult(null);
    setError(null);
  }, [data]);

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
      // Uses the rows already in memory - no second fetch from SAP.
      const output = await processFn(data);
      downloadBlob(output.blob, output.filename);
      setResult(output);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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

      {result && result.warningCount === 0 && (
        <p className="text-xs text-emerald-600">
          Processed {result.recordCount} row{result.recordCount === 1 ? "" : "s"} with no
          warnings. Downloaded {result.filename}. S/4 push is not connected yet.
        </p>
      )}
      {result && result.warningCount > 0 && (
        <p className="text-xs text-amber-600">
          Processed {result.recordCount} row{result.recordCount === 1 ? "" : "s"} with{" "}
          {result.warningCount} warning{result.warningCount === 1 ? "" : "s"}. See the
          &quot;Warnings&quot; sheet in {result.filename}. Nothing was pushed to S/4.
        </p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

export default ProcessButton;