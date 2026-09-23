import { useState } from "react";

// Mirrors backend/services/mappings.py. There's no endpoint exposing these
// yet, so they're mirrored here as static reference data -- if mappings.py
// changes, update this list too. (Worth turning into a GET /ar/mappings
// endpoint later so the two can't drift apart.)
const MAPPING_GROUPS = [
  {
    id: "company_code",
    label: "Company Code",
    columns: ["ECC", "S/4"],
    rows: [["US01", "1000"]],
  },
  {
    id: "payment_terms",
    label: "Payment Terms",
    columns: ["ECC", "S/4"],
    rows: [
      ["0002", "Z001"],
      ["0003", "Z002"],
      ["0004", "Z003"],
      ["0006", "Z004"],
    ],
  },
  {
    id: "customer",
    label: "Customer",
    columns: ["ECC Customer", "S/4 Business Partner"],
    rows: [
      ["100000", "10000131"],
      ["100001", "10000132"],
      ["100002", "10000133"],
      ["100003", "10000134"],
    ],
  },
];

// Document type isn't a lookup table -- every row is hardcoded to "UE"
// regardless of the ECC document type, so it's called out separately.
const DOCUMENT_TYPE = "UE";

function MappingTable({ group }) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <table className="min-w-full text-xs">
        <thead className="bg-[#0B1F3A] text-white">
          <tr>
            {group.columns.map((col) => (
              <th key={col} className="px-3 py-2 text-left font-medium whitespace-nowrap">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {group.rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
              {row.map((cell, j) => (
                <td
                  key={j}
                  className="px-3 py-2 whitespace-nowrap border-t border-gray-100 font-mono text-[#0B1F3A]"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * MappingsPanel
 *
 * Static reference panel showing the ECC -> S/4 lookup tables the
 * processor applies (mappings.py). Meant to sit alongside DataPreview so
 * users can see what a fetched row will translate to before running
 * "Process".
 */
function MappingsPanel() {
  const [activeGroup, setActiveGroup] = useState(MAPPING_GROUPS[0].id);
  const current = MAPPING_GROUPS.find((g) => g.id === activeGroup);

  return (
    <div className="flex flex-col gap-3 border border-gray-200 rounded-lg p-4 w-full lg:w-72 shrink-0">
      <div>
        <h2 className="text-sm font-medium text-gray-700">Mappings Used</h2>
        <p className="text-xs text-gray-500">
          ECC → S/4 lookups applied during processing.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {MAPPING_GROUPS.map((group) => {
          const isSelected = activeGroup === group.id;
          return (
            <button
              key={group.id}
              onClick={() => setActiveGroup(group.id)}
              className={`px-3 py-1.5 rounded-lg text-xs border transition-colors cursor-pointer ${
                isSelected
                  ? "bg-[#0B1F3A] text-white border-[#0B1F3A]"
                  : "bg-white text-gray-700 border-gray-300 hover:border-[#0B1F3A]"
              }`}
            >
              {group.label}
            </button>
          );
        })}
      </div>

      <div className="max-h-[50vh] overflow-auto">
        <MappingTable group={current} />
      </div>

      <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
        <p className="text-xs text-gray-500">Document Type</p>
        <p className="text-sm text-[#0B1F3A] font-mono">{DOCUMENT_TYPE}</p>
        <p className="text-xs text-gray-400 mt-1">
          Every row loads as {DOCUMENT_TYPE}, regardless of the ECC document type.
        </p>
      </div>
    </div>
  );
}

export default MappingsPanel;
