import { useState } from "react";
import { fetchARData } from "../../api/client";

const Fetch_func = {
  ar: fetchARData,
};

function FetchDataButton({ process, onDataFetched, loading, setLoading }) {
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleClick = async () => {
    const fetchFn = Fetch_func[process];
    if (!fetchFn) {
      setError(`No fetch wired up yet for "${process}"`);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetchFn();
      // Backend returns { status, file, record_count, records: [...] }
      setResult(response);
      onDataFetched(response);
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
        disabled={loading}
        className="px-5 py-2.5 bg-[#0B1F3A] text-white rounded-lg disabled:opacity-60"
      >
        {loading ? "Fetching..." : "Fetch Data"}
      </button>

      {result && !error && (
        <p className="text-xs text-emerald-600">
          Fetched {result.record_count} row{result.record_count === 1 ? "" : "s"}.
          Staged as <span className="font-mono">{result.file}</span>.
        </p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

export default FetchDataButton;