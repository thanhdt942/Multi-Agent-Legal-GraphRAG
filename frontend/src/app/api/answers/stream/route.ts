export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API_BASE_URL = (process.env.API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export async function POST(request: Request): Promise<Response> {
  let upstream: Response;
  try {
    upstream = await fetch(`${API_BASE_URL}/v1/answers:stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: await request.text(),
      cache: "no-store",
      signal: request.signal,
    });
  } catch {
    return Response.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: "Không thể kết nối FastAPI." } },
      { status: 503 },
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
