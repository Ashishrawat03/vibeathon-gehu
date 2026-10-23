import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function PUT(
  req: NextRequest,
  context: { params: Promise<{ outputId: string }> },
) {
  try {
    const { outputId } = await context.params;
    const authorization = req.headers.get("authorization");
    const res = await fetch(
      `${BACKEND_URL}/api/v1/transform/outputs/${encodeURIComponent(outputId)}/feedback`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(authorization ? { authorization } : {}),
        },
        body: await req.text(),
      },
    );
    return NextResponse.json(await res.json(), { status: res.status });
  } catch (err) {
    return NextResponse.json(
      { detail: "Backend unavailable", error: String(err) },
      { status: 503 },
    );
  }
}
