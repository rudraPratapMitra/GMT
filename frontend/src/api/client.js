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