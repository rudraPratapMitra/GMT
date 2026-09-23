// // const BASE_URL = "http://localhost:8000";

// // async function request(path, options = {}) {
// //   const response = await fetch(`${BASE_URL}${path}`, {
// //     headers: { Accept: "application/json", ...options.headers },
// //     ...options,
// //   });

// //   if (!response.ok) {
// //     let message = `Request failed with status ${response.status}`;
// //     try {
// //       const { detail } = await response.json();
// //       if (typeof detail === "string") message = detail;
// //       else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join("; ");
// //     } catch {
// //       /* not JSON — keep generic */
// //     }
// //     throw new Error(message);
// //   }

// //   return response.json();
// // }

// // // Step 1 — fetch ECC rows, backend stages an Excel into ECC_DATA/.
// // // Returns: { status, file, record_count, records: [...] }
// // export async function fetchARData() {
// //   return request("/ar/ecc_data");
// // }

// // // Step 2 — transform the staged ECC file into the S/4 template.
// // // No body; backend reads ECC_DATA/ itself.
// // // Returns: { status, file, row_count, warning_count }
// // export async function processARData() {
// //   return request("/ar/process", { method: "POST" });
// // }

// // // Step 3 — cheap preview for the Validate page. No workbook read.
// // // Returns: { ecc: {name,size,modified}|null, s4: {...}|null }
// // export async function getLatestFiles() {
// //   return request("/ar/validate/latest");
// // }

// // // Step 4 — run all checks.
// // // Returns: { process, overall_status, summary, checks: [...] }
// // export async function validateAR() {
// //   return request("/ar/validate", { method: "POST" });
// // }

// // // Step 5 — push staged S/4 rows via OData.
// // // Returns: { status, success_count, error_count, errors }
// // export async function loadToS4() {
// //   return request("/ar/load-to-s4", { method: "POST" });
// // }


// // // Step 6 — download the PDF validation report for the currently staged
// // // files. Bypasses `request()` since the response body is a PDF blob, not
// // // JSON, on success.
// // export async function downloadValidationReport() {
// //   const response = await fetch(`${BASE_URL}/ar/validate/report`);

// //   if (!response.ok) {
// //     let message = `Request failed with status ${response.status}`;
// //     try {
// //       const { detail } = await response.json();
// //       if (typeof detail === "string") message = detail;
// //       else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join("; ");
// //     } catch {
// //       /* not JSON — keep generic */
// //     }
// //     throw new Error(message);
// //   }

// //   return response.blob();
// // }

// export const BASE_URL = "http://localhost:8000";

// async function request(path, options = {}) {
//   const response = await fetch(`${BASE_URL}${path}`, {
//     headers: { Accept: "application/json", ...options.headers },
//     ...options,
//   });

//   if (!response.ok) {
//     let message = `Request failed with status ${response.status}`;
//     try {
//       const { detail } = await response.json();
//       if (typeof detail === "string") message = detail;
//       else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join("; ");
//     } catch {
//       /* not JSON — keep generic */
//     }
//     throw new Error(message);
//   }

//   return response.json();
// }

// // Connection indicator — pings the backend's /health endpoint.
// // Returns true/false rather than throwing, since a failed health check is
// // an expected, routine outcome (backend not started yet, etc.), not an error.
// export async function checkHealth() {
//   try {
//     const response = await fetch(`${BASE_URL}/health`);
//     return response.ok;
//   } catch {
//     return false;
//   }
// }

// // Step 1 — fetch ECC rows, backend stages an Excel into ECC_DATA/.
// // Returns: { status, file, record_count, records: [...] }
// export async function fetchARData() {
//   return request("/ar/ecc_data");
// }

// // Step 2 — transform the staged ECC file into the S/4 template.
// // No body; backend reads ECC_DATA/ itself.
// // Returns: { status, file, row_count, warning_count }
// export async function processARData() {
//   return request("/ar/process", { method: "POST" });
// }

// // Step 3 — cheap preview for the Validate page. No workbook read.
// // Returns: { ecc: {name,size,modified}|null, s4: {...}|null }
// export async function getLatestFiles() {
//   return request("/ar/validate/latest");
// }

// // Step 4 — run all checks.
// // Returns: { process, overall_status, summary, checks: [...] }
// export async function validateAR() {
//   return request("/ar/validate", { method: "POST" });
// }

// // Step 5 — push staged S/4 rows via OData.
// // Returns: { status, success_count, error_count, errors }
// export async function loadToS4() {
//   return request("/ar/load-to-s4", { method: "POST" });
// }

// // Step 6 — download the PDF validation report for the currently staged
// // files. Bypasses `request()` since the response body is a PDF blob, not
// // JSON, on success.
// export async function downloadValidationReport() {
//   const response = await fetch(`${BASE_URL}/ar/validate/report`);

//   if (!response.ok) {
//     let message = `Request failed with status ${response.status}`;
//     try {
//       const { detail } = await response.json();
//       if (typeof detail === "string") message = detail;
//       else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join("; ");
//     } catch {
//       /* not JSON — keep generic */
//     }
//     throw new Error(message);
//   }

//   return response.blob();
// }

export const BASE_URL = "http://localhost:8000";

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

// Connection indicator — pings the backend's /health endpoint.
// Returns true/false rather than throwing, since a failed health check is
// an expected, routine outcome (backend not started yet, etc.), not an error.
export async function checkHealth() {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// Step 1 — fetch ECC rows, backend stages an Excel into ECC_DATA/.
// Returns: { status, file, record_count, records: [...] }
export async function fetchARData() {
  return request("/ar/ecc_data");
}

// Step 2 — transform the staged ECC file into the S/4 template.
// No body; backend reads ECC_DATA/ itself.
// Returns: { status, file, row_count, warning_count, currency_mismatches }
export async function processARData() {
  return request("/ar/process", { method: "POST" });
}

// Step 2b — remove rows flagged as currency exceptions from the staged
// ECC file, then reprocess. `recordIndices` are the `record` numbers from
// a processARData() response's currency_mismatches, passed through as-is.
// Returns the same shape as processARData().
export async function deleteMismatchesAndProcess(recordIndices) {
  return request("/ar/process/delete-mismatches", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ record_indices: recordIndices }),
  });
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

// Step 6 — download the PDF validation report for the currently staged
// files. Bypasses `request()` since the response body is a PDF blob, not
// JSON, on success.
export async function downloadValidationReport() {
  const response = await fetch(`${BASE_URL}/ar/validate/report`);

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

  return response.blob();
}