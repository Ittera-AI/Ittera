"use client";

import { useEffect, useState } from "react";
import { FileText } from "lucide-react";

import { ProductShell } from "@/components/product/ProductShell";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useProduct } from "@/hooks/useProduct";
import type { Suggestion } from "@/services/product.service";

export default function CreatePage() {
  const product = useProduct();
  const loadDashboard = product.loadDashboard;
  const loadTrends = product.loadTrends;
  const loadDrafts = product.loadDrafts;
  const [platform, setPlatform] = useState("linkedin");
  const [prompt, setPrompt] = useState("");
  const [draftPickerOpen, setDraftPickerOpen] = useState(false);

  useEffect(() => {
    void loadDashboard();
    void loadTrends();
    void loadDrafts();
  }, [loadDashboard, loadDrafts, loadTrends]);

  /** Radar → Create handoff via localStorage (defer setState to avoid sync effect updates). */
  useEffect(() => {
    const t = window.setTimeout(() => {
      try {
        const fromRadar = window.localStorage.getItem("ittera-radar-prompt");
        if (fromRadar?.trim()) {
          setPrompt(fromRadar.trim());
          window.localStorage.removeItem("ittera-radar-prompt");
        }
      } catch {
        /* private mode / blocked storage */
      }
    }, 0);
    return () => window.clearTimeout(t);
  }, []);

  const locked = product.brandProfile?.is_confirmed !== true;
  const draft = product.currentDraft;
  const limit = platform === "twitter" ? 280 : platform === "instagram" ? 2200 : 3000;

  function applySuggestion(suggestion: Suggestion) {
    setPrompt(`${suggestion.hook}\n\n${suggestion.angle}`);
    void product.generate(platform, `${suggestion.hook}\n\n${suggestion.angle}`, suggestion.trend_tie, suggestion);
  }

  function tomorrowMorning() {
    const date = new Date();
    date.setDate(date.getDate() + 1);
    date.setHours(9, 0, 0, 0);
    return date.toISOString();
  }

  return (
    <ProductShell>
      <section className="flex flex-col gap-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Create</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">Turn signal into a draft</h1>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Trends, brand voice, and drafts live in one workspace so creation feels directed instead of blank.
            </p>
          </div>
          <Sheet open={draftPickerOpen} onOpenChange={setDraftPickerOpen}>
            <SheetTrigger render={<Button type="button" variant="outline" className="gap-2 shrink-0" />}>
              <FileText size={14} aria-hidden />
              Drafts ({product.drafts.length})
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Your drafts</SheetTitle>
              </SheetHeader>
              <div className="mt-4 flex flex-col gap-2">
                {product.drafts.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No drafts yet. Generate one from the studio.</p>
                ) : (
                  product.drafts.map((d) => (
                    <button
                      key={d.id}
                      type="button"
                      className="rounded-lg border p-3 text-left text-sm transition-all hover:bg-muted active:scale-[0.99]"
                      onClick={() => {
                        product.selectDraft(d.id);
                        setDraftPickerOpen(false);
                      }}
                    >
                      <p className="line-clamp-2 font-medium">{(d.content ?? "").split("\n")[0] || "Untitled draft"}</p>
                      <p className="mt-1 text-xs capitalize text-muted-foreground">
                        {d.platform} · {d.status}
                      </p>
                    </button>
                  ))
                )}
              </div>
            </SheetContent>
          </Sheet>
        </header>

        {locked ? (
          <Alert>
            <AlertTitle>Brand Profile required</AlertTitle>
            <AlertDescription>Confirm your Brand Profile on the dashboard before generating content.</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
          <Card>
            <CardHeader>
              <CardTitle>Prompt studio</CardTitle>
              <CardDescription>Choose a platform, pick a trend, or ask for suggestions.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5">
              <Tabs value={platform} onValueChange={setPlatform}>
                <TabsList>
                  <TabsTrigger value="linkedin">LinkedIn</TabsTrigger>
                  <TabsTrigger value="instagram">Instagram</TabsTrigger>
                  <TabsTrigger value="twitter">X</TabsTrigger>
                </TabsList>
              </Tabs>

              <FieldGroup>
                <Field>
                  <FieldLabel>What do you want to write about?</FieldLabel>
                  <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="A point of view, a trend, or a half-formed idea..." />
                </Field>
              </FieldGroup>

              <div className="flex flex-wrap gap-2">
                {product.trends?.trends.slice(0, 5).map((trend) => (
                  <button
                    key={trend.topic}
                    className="rounded-md border bg-background px-3 py-2 text-sm transition-refined active:scale-[0.98]"
                    onClick={() => setPrompt(trend.content_angle)}
                    type="button"
                  >
                    {trend.topic}
                  </button>
                ))}
              </div>

              <div className="flex flex-wrap gap-3">
                <Button disabled={locked || product.isLoading} onClick={() => void product.suggest(platform, prompt || undefined)}>
                  Suggest for me
                </Button>
                <Button disabled={locked || !prompt || product.isLoading} variant="outline" onClick={() => void product.generate(platform, prompt)}>
                  Generate draft
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Draft editor</CardTitle>
              <CardDescription>
                {draft ? `${(draft.content ?? "").length}/${limit} characters` : "Generated content appears here."}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {product.suggestions.length ? (
                <div className="grid gap-3">
                  {product.suggestions.map((suggestion) => (
                    <button
                      key={suggestion.hook}
                      className="rounded-lg border bg-muted/30 p-4 text-left transition-refined hover:bg-muted active:scale-[0.99]"
                      onClick={() => applySuggestion(suggestion)}
                      type="button"
                    >
                      <p className="font-medium">{suggestion.hook}</p>
                      <p className="mt-1 text-sm text-muted-foreground">{suggestion.why_it_works}</p>
                    </button>
                  ))}
                </div>
              ) : null}

              <Textarea className="min-h-80" readOnly value={draft?.content ?? ""} placeholder="Your generated draft will appear here." />

              <div className="flex flex-wrap gap-3">
                <Sheet>
                  <SheetTrigger render={<Button disabled={!draft} variant="outline" />}>
                    Repurpose
                  </SheetTrigger>
                  <SheetContent>
                    <SheetHeader>
                      <SheetTitle>Repurpose draft</SheetTitle>
                    </SheetHeader>
                    <div className="mt-6 flex flex-col gap-3">
                      <Button onClick={() => void product.repurpose("instagram")}>Create Instagram version</Button>
                      <Button onClick={() => void product.repurpose("twitter")} variant="outline">Create X thread</Button>
                      {draft ? Object.entries(draft.repurposed_versions ?? {}).map(([target, content]) => (
                        <div key={target} className="rounded-lg border p-3 text-sm">
                          <p className="font-medium capitalize">{target}</p>
                          <p className="mt-2 whitespace-pre-wrap text-muted-foreground">{content}</p>
                        </div>
                      )) : null}
                    </div>
                  </SheetContent>
                </Sheet>
                <Button disabled={!draft} onClick={() => draft && void product.publish(draft.id)}>Publish now</Button>
                <Button disabled={!draft} variant="outline" onClick={() => draft && void product.schedule(draft.id, tomorrowMorning())}>
                  Schedule tomorrow
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </ProductShell>
  );
}
