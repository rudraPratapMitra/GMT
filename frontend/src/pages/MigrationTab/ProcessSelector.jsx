const PROCESSES = [
  { id: "ar", label: "Accounts Receivable" },
  { id: "ap", label: "Accounts Payable" },
  { id: "assets", label: "Assets" },
  { id: "credit", label: "Credit Management" },
];

const ACTIVE_PROCESSES = ["ar"];

function ProcessSelector({ selectedProcess, onProcessChange }) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-medium text-gray-700">Process</h2>
      <div className="flex gap-2">
        {PROCESSES.map((proc) => {
          const isActive = ACTIVE_PROCESSES.includes(proc.id);
          const isSelected = selectedProcess === proc.id;

          return (
            <button
              key={proc.id}
              onClick={() => isActive && onProcessChange(proc.id)}
              disabled={!isActive}
              title={!isActive ? "Coming soon" : undefined}
              className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                isSelected
                  ? "bg-[#0B1F3A] text-white border-[#0B1F3A]"
                  : "bg-white text-gray-700 border-gray-300"
              } ${
                !isActive
                  ? "opacity-40 cursor-not-allowed"
                  : "hover:border-[#0B1F3A] cursor-pointer"
              }`}
            >
              {proc.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default ProcessSelector;