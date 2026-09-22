import { useState } from "react";
import ProcessSelector from "./ProcessSelector";
import FetchDataButton from "./FetchDataButton";
import ProcessButton from "./ProcessButton";
import DataPreview from "./DataPreview";

function MigrationPage() {
  const [process, setProcess] = useState("ar");
  const [fetchResult, setFetchResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const records = fetchResult?.records ?? [];
  const hasData = records.length > 0;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-[#0B1F3A]">ECC → S/4 Migration</h1>
        <p className="text-sm text-gray-500">
          Fetch, review, and push data through the migration pipeline.
        </p>
      </div>

      <div className="flex flex-col gap-4 border border-gray-200 rounded-lg p-5">
        <ProcessSelector selectedProcess={process} onProcessChange={setProcess} />
        <FetchDataButton
          process={process}
          onDataFetched={setFetchResult}
          loading={loading}
          setLoading={setLoading}
        />
      </div>

      <DataPreview data={records} loading={loading} />
      <ProcessButton hasData={hasData} process={process} />
    </div>
  );
}

export default MigrationPage;