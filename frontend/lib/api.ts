const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type HealthResponse = {
  status: string;
  version: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`, {
    next: { revalidate: 0 },
  });

  if (!res.ok) {
    throw new Error("Impossible de joindre l'API");
  }

  return res.json();
}
