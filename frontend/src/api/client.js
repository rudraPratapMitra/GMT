// const BASE_URL = "http://localhost:8000";

// async function request(path) {
//   const url = `${BASE_URL}${path}`;
//   const response = await fetch(url, {
//     headers: { Accept: "application/json" },
//   });

//   if (!response.ok) {
//     let detail = `Request failed with status ${response.status}`;
//     throw new Error(detail);
//   }

//   return response.json();
// }

// export async function fetchARData() {
//   return request("/ar/ecc_data");
// }

const BASE_URL = "http://localhost:8000";

async function request(path) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return response.json();
}

export async function fetchARData() {
  return request("/ar/ecc_data");
}

/**
 * Sends the already-fetched ECC rows to POST /ar/process (the backend does not
 * call SAP again) and resolves with the generated S/4 workbook plus the
 * summary the backend puts in the response headers.
 *
 * Not built on request(): that helper is GET + JSON only, and this call needs
 * a POST body and a binary (.xlsx) response.
 */
export async function processARData(records) {
  const response = await fetch(`${BASE_URL}/ar/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ records }),
  });

  if (!response.ok) {
    let message = `Processing failed with status ${response.status}`;
    try {
      // FastAPI: {detail: "text"} for our errors, {detail: [{msg, loc}, ...]} for validation errors
      const { detail } = await response.json();
      if (typeof detail === "string") message = detail;
      else if (Array.isArray(detail)) message = detail.map((d) => d.msg).join("; ");
    } catch {
      /* response wasn't JSON - keep the generic message */
    }
    throw new Error(message);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const filename = /filename="?([^";]+)"?/.exec(disposition)?.[1] ?? "AR_S4_Load.xlsx";

  return {
    blob: await response.blob(),
    filename,
    recordCount: Number(response.headers.get("X-Record-Count") ?? 0),
    warningCount: Number(response.headers.get("X-Warning-Count") ?? 0),
    s4Push: response.headers.get("X-S4-Push") ?? "",
  };
}