export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API_BASE_URL = (process.env.API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function GET(): Promise<Response> {
  try {
    const response = await fetch(`${API_BASE_URL}/v1/health`, { cache: "no-store" });
    return new Response(response.body, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return Response.json({ status: "unavailable" }, { status: 503 });
  }
}
