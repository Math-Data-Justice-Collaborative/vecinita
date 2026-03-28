// @ts-nocheck
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

type SearchPayload = {
  query?: string;
  query_embedding?: number[];
  match_threshold?: number;
  match_count?: number;
  tag_filter?: string[];
  tag_match_mode?: "any" | "all";
  include_untagged_fallback?: boolean;
};

async function runSearchRpc(
  supabaseAdmin: ReturnType<typeof createClient>,
  params: {
    query_embedding: number[];
    match_threshold: number;
    match_count: number;
    tag_filter: string[];
    tag_match_mode: "any" | "all";
    include_untagged_fallback: boolean;
  },
) {
  const primary = await supabaseAdmin
    .schema("graphql_public")
    .rpc("search_similar_documents", params);

  if (!primary.error) {
    return primary;
  }

  const message = String(primary.error.message ?? "").toLowerCase();
  const canFallbackToPublic =
    message.includes("schema") ||
    message.includes("pgrst106") ||
    message.includes("not found") ||
    message.includes("does not exist");

  if (!canFallbackToPublic) {
    return primary;
  }

  return await supabaseAdmin
    .schema("public")
    .rpc("search_similar_documents", params);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

    if (!supabaseUrl || !serviceRoleKey) {
      return new Response(
        JSON.stringify({ error: "Supabase service role environment is not configured" }),
        {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        },
      );
    }

    const payload = (await req.json()) as SearchPayload;
    const queryEmbedding = Array.isArray(payload.query_embedding)
      ? payload.query_embedding.filter((value) => Number.isFinite(value))
      : [];

    if (!queryEmbedding.length) {
      return new Response(JSON.stringify({ data: [] }), {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const matchThreshold = Number.isFinite(payload.match_threshold)
      ? Number(payload.match_threshold)
      : 0.3;
    const matchCount = Number.isFinite(payload.match_count)
      ? Number(payload.match_count)
      : 5;

    const tagFilter = Array.isArray(payload.tag_filter)
      ? payload.tag_filter.filter((value) => typeof value === "string" && value.length > 0)
      : [];

    const tagMatchMode = payload.tag_match_mode === "all" ? "all" : "any";
    const includeUntaggedFallback = payload.include_untagged_fallback !== false;

    const supabaseAdmin = createClient(supabaseUrl, serviceRoleKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    });

    const { data, error } = await runSearchRpc(supabaseAdmin, {
      query_embedding: queryEmbedding,
      match_threshold: matchThreshold,
      match_count: matchCount,
      tag_filter: tagFilter,
      tag_match_mode: tagMatchMode,
      include_untagged_fallback: includeUntaggedFallback,
    });

    if (error) {
      return new Response(JSON.stringify({ error: error.message, details: error }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const rows = Array.isArray(data) ? data : [];
    return new Response(JSON.stringify({ data: rows }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: "search-similar-documents function failed",
        details: error instanceof Error ? error.message : String(error),
      }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      },
    );
  }
});
