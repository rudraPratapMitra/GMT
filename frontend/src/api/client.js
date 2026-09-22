const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { Accept: "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const { detail } = await response.json();
      if (typeof detail === "string") message = detail;
      else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join("; ");
    } catch {
      /* not JSON — keep generic */
    }
    throw new Error(message);
  }

  return response.json();
}

// Step 1 — fetch ECC rows, backend stages an Excel into ECC_DATA/.
// Returns: { status, file, record_count, records: [...] }
export async function fetchARData() {
  return request("/ar/ecc_data");
}

// Step 2 — transform the staged ECC file into the S/4 template.
// No body; backend reads ECC_DATA/ itself.
// Returns: { status, file, row_count, warning_count }
export async function processARData() {
  return request("/ar/process", { method: "POST" });
}

// Step 3 — cheap preview for the Validate page. No workbook read.
// Returns: { ecc: {name,size,modified}|null, s4: {...}|null }
export async function getLatestFiles() {
  return request("/ar/validate/latest");
}

// Step 4 — run all checks.
// Returns: { process, overall_status, summary, checks: [...] }
export async function validateAR() {
  return request("/ar/validate", { method: "POST" });
}

// Step 5 — push staged S/4 rows via OData.
// Returns: { status, success_count, error_count, errors }
export async function loadToS4() {
  return request("/ar/load-to-s4", { method: "POST" });
}