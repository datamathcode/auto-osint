"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

type ScopeForm = {
  target_name: string;
  claim_under_investigation: string;
  start_date: string;
  end_date: string;
  platforms: string[];
  data_types: string[];
  max_execution_minutes: number;
};

type ConfigForm = {
  llm_provider: string;
  llm_api_key: string;
  breach_api_key: string;
  synint_path: string;
};

type Defaults = {
  llm: { provider: string; providers: string[]; has_api_key: boolean; ollama_base_url: string };
  openosint: { has_breach_key: boolean };
  synint: { path: string };
  database: { url: string; server_side: boolean };
  limits: {
    max_execution_time_seconds: number;
    timeout_per_tool_seconds: number;
    max_concurrent_queries: number;
  };
};

const STORAGE_KEY = "auto-osint-config";

const PLATFORMS = ["twitter", "linkedin", "github", "reddit", "instagram", "facebook"];
const DATA_TYPES = ["filings", "news", "academic", "registries", "breach", "social"];

const FIELD =
  "mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none";

export default function InvestigatePage() {
  const router = useRouter();
  const [defaults, setDefaults] = useState<Defaults | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [runNow, setRunNow] = useState(true);

  const scopeForm = useForm<ScopeForm>({
    defaultValues: {
      target_name: "",
      claim_under_investigation: "",
      start_date: "",
      end_date: "",
      platforms: ["github"],
      data_types: ["news"],
      max_execution_minutes: 60,
    },
  });

  const configForm = useForm<ConfigForm>({
    defaultValues: {
      llm_provider: "anthropic",
      llm_api_key: "",
      breach_api_key: "",
      synint_path: "synint",
    },
  });

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    fetch(`${base}/api/config/defaults`)
      .then((response) => (response.ok ? response.json() : null))
      .then((payload: Defaults | null) => {
        if (!payload) return;
        setDefaults(payload);

        const stored = window.localStorage.getItem(STORAGE_KEY);
        const saved = stored ? (JSON.parse(stored) as Partial<ConfigForm>) : {};
        configForm.reset({
          llm_provider: saved.llm_provider ?? payload.llm.provider,
          llm_api_key: saved.llm_api_key ?? "",
          breach_api_key: saved.breach_api_key ?? "",
          synint_path: saved.synint_path ?? payload.synint.path,
        });
      })
      .catch(() => setDefaults(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const subscription = configForm.watch((values) => {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(values));
    });
    return () => subscription.unsubscribe();
  }, [configForm]);

  const onSubmit = async (values: ScopeForm) => {
    setSubmitError(null);
    setSubmitting(true);
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

    try {
      const createResponse = await fetch(`${base}/api/investigations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_name: values.target_name,
          claim_under_investigation: values.claim_under_investigation,
          scope: {
            start_date: values.start_date || null,
            end_date: values.end_date || null,
            platforms: values.platforms,
            data_types: values.data_types,
            max_execution_minutes: Number(values.max_execution_minutes),
          },
        }),
      });

      if (!createResponse.ok) {
        const detail = await createResponse.text();
        throw new Error(`Create failed (${createResponse.status}): ${detail}`);
      }

      const investigation = (await createResponse.json()) as { id: number };

      if (runNow) {
        const runResponse = await fetch(`${base}/api/orchestrate/async`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ investigation_id: investigation.id }),
        });
        if (!runResponse.ok) {
          // The investigation exists; report the run failure but keep the link.
          setSubmitError(
            `Investigation #${investigation.id} created, but the run failed (${runResponse.status}).`,
          );
          router.push(`/investigations/${investigation.id}/progress`);
          return;
        }
      }

      router.push(
        runNow ? `/investigations/${investigation.id}/progress` : `/dossiers/${investigation.id}`,
      );
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Unexpected error");
    } finally {
      setSubmitting(false);
    }
  };

  const missingBreachKey = defaults ? !defaults.openosint.has_breach_key : false;

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold">New investigation</h1>
      <p className="mt-1 text-sm text-gray-600">
        Describes the target and the claim. Scope narrows what the agents query.
      </p>

      {missingBreachKey && (
        <p className="mt-4 rounded border-l-4 border-amber-500 bg-amber-50 p-3 text-sm text-amber-900">
          <code>HIBP_API_KEY</code> is not set on the server. Breach lookups will be
          skipped and reported as gaps.
        </p>
      )}

      <form className="mt-6 space-y-6" onSubmit={scopeForm.handleSubmit(onSubmit)}>
        <section className="space-y-4">
          <div>
            <label className="text-sm font-medium" htmlFor="target_name">
              Target name *
            </label>
            <input
              id="target_name"
              className={FIELD}
              placeholder="johndoe or example.com"
              {...scopeForm.register("target_name", { required: "Target name is required" })}
            />
            {scopeForm.formState.errors.target_name && (
              <p className="mt-1 text-xs text-red-600">
                {scopeForm.formState.errors.target_name.message}
              </p>
            )}
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="claim">
              Claim to investigate *
            </label>
            <textarea
              id="claim"
              rows={3}
              className={FIELD}
              placeholder="Find all social accounts for johndoe"
              {...scopeForm.register("claim_under_investigation", {
                required: "A claim is required",
                minLength: { value: 5, message: "Describe the claim in at least 5 characters" },
              })}
            />
            {scopeForm.formState.errors.claim_under_investigation && (
              <p className="mt-1 text-xs text-red-600">
                {scopeForm.formState.errors.claim_under_investigation.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium" htmlFor="start_date">
                Start date
              </label>
              <input id="start_date" type="date" className={FIELD} {...scopeForm.register("start_date")} />
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="end_date">
                End date
              </label>
              <input
                id="end_date"
                type="date"
                className={FIELD}
                {...scopeForm.register("end_date", {
                  validate: (value) => {
                    const start = scopeForm.getValues("start_date");
                    if (!value || !start) return true;
                    return value >= start || "End date must be on or after the start date";
                  },
                })}
              />
              {scopeForm.formState.errors.end_date && (
                <p className="mt-1 text-xs text-red-600">
                  {scopeForm.formState.errors.end_date.message}
                </p>
              )}
            </div>
          </div>

          <fieldset>
            <legend className="text-sm font-medium">Platforms to query</legend>
            <div className="mt-2 flex flex-wrap gap-3">
              {PLATFORMS.map((platform) => (
                <label key={platform} className="inline-flex items-center gap-2 text-sm">
                  <input type="checkbox" value={platform} {...scopeForm.register("platforms")} />
                  {platform}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-sm font-medium">Data types</legend>
            <div className="mt-2 flex flex-wrap gap-3">
              {DATA_TYPES.map((dataType) => (
                <label key={dataType} className="inline-flex items-center gap-2 text-sm">
                  <input type="checkbox" value={dataType} {...scopeForm.register("data_types")} />
                  {dataType}
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label className="text-sm font-medium" htmlFor="max_execution_minutes">
              Max execution time: {scopeForm.watch("max_execution_minutes")} minutes
            </label>
            <input
              id="max_execution_minutes"
              type="range"
              min={5}
              max={60}
              step={5}
              className="mt-1 w-full"
              {...scopeForm.register("max_execution_minutes", { valueAsNumber: true })}
            />
          </div>
        </section>

        <section className="space-y-4 border-t pt-6">
          <h2 className="text-lg font-semibold">Configuration</h2>
          <p className="text-xs text-gray-600">
            Key values are stored only in this browser (localStorage). The database URL is
            server-side and cannot be set here.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium" htmlFor="llm_provider">
                LLM provider
              </label>
              <select id="llm_provider" className={FIELD} {...configForm.register("llm_provider")}>
                {(defaults?.llm.providers ?? ["anthropic", "openai", "ollama"]).map((provider) => (
                  <option key={provider} value={provider}>
                    {provider}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="llm_api_key">
                LLM API key
              </label>
              <input
                id="llm_api_key"
                type="password"
                autoComplete="off"
                className={FIELD}
                placeholder={defaults?.llm.has_api_key ? "already set server-side" : "sk-..."}
                {...configForm.register("llm_api_key")}
              />
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="breach_api_key">
                Breach API key (HIBP)
              </label>
              <input
                id="breach_api_key"
                type="password"
                autoComplete="off"
                className={FIELD}
                {...configForm.register("breach_api_key")}
              />
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="synint_path">
                SYNINT binary path
              </label>
              <input id="synint_path" className={FIELD} {...configForm.register("synint_path")} />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium" htmlFor="database_url">
              Database (server-side)
            </label>
            <input
              id="database_url"
              className={`${FIELD} bg-gray-100 text-gray-500`}
              value={defaults?.database.url ?? "loading..."}
              readOnly
              disabled
            />
          </div>

          <label className="inline-flex items-center gap-2 text-sm">
            <input type="checkbox" checked={runNow} onChange={(event) => setRunNow(event.target.checked)} />
            Run the investigation immediately after creating it
          </label>
        </section>

        {submitError && (
          <p className="rounded border-l-4 border-red-500 bg-red-50 p-3 text-sm text-red-800">
            {submitError}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Starting..." : "Start investigation"}
        </button>
      </form>
    </main>
  );
}
