"use client";

import { useEffect, useState } from "react";
import { FileText, ImagePlus, Save, Trash2, Sparkles, Loader2 } from "lucide-react";

import { AuthenticatedImage } from "@/components/product/AuthenticatedImage";
import { ProductShell } from "@/components/product/ProductShell";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useProduct } from "@/hooks/useProduct";
import type { Suggestion } from "@/services/product.service";

function toDatetimeLocal(value: string) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

export default function CreatePage() {
  const product = useProduct();
  const loadDashboard = product.loadDashboard;
  const loadTrends = product.loadTrends;
  const loadDrafts = product.loadDrafts;
  const [platform, setPlatform] = useState("linkedin");
  const [prompt, setPrompt] = useState("");
  const [draftBody, setDraftBody] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");
  const [draftPickerOpen, setDraftPickerOpen] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    void loadDashboard().catch(() => undefined);
    void loadTrends().catch(() => undefined);
    void loadDrafts().catch(() => undefined);
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

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDraftBody(draft?.content ?? "");
      setScheduleAt(draft?.scheduled_for ? toDatetimeLocal(draft.scheduled_for) : "");
    }, 0);
    return () => window.clearTimeout(timer);
  }, [draft?.id, draft?.content, draft?.scheduled_for]);

  function applySuggestion(suggestion: Suggestion) {
    setPrompt(`${suggestion.hook}\n\n${suggestion.angle}`);
    void product.generate(platform, `${suggestion.hook}\n\n${suggestion.angle}`, suggestion.trend_tie, suggestion);
  }

  function tomorrowMorning() {
    const date = new Date();
    date.setDate(date.getDate() + 1);
    date.setHours(9, 0, 0, 0);
    return toDatetimeLocal(date.toISOString());
  }

  async function saveDraft() {
    if (!draft) return;
    await product.updateDraft(draft.id, { content: draftBody });
  }

  async function uploadImages(files: FileList | null) {
    if (!draft || !files?.length) return;
    setUploadError(null);
    const existing = draft.media?.length ?? 0;
    const selected = Array.from(files);
    if (existing + selected.length > 4) {
      setUploadError("A draft can have up to 4 images. Remove one before adding more.");
      return;
    }
    const invalid = selected.find((file) => !["image/jpeg", "image/png", "image/webp"].includes(file.type));
    if (invalid) {
      setUploadError("Only JPEG, PNG, and WebP images are supported.");
      return;
    }
    for (const file of selected) {
      await product.uploadDraftMedia(draft.id, file);
    }
  }

  async function scheduleDraft() {
    const timeToSchedule = scheduleAt || tomorrowMorning();
    if (!draft || !timeToSchedule) return;
    if (draftBody !== (draft.content ?? "")) {
      await product.updateDraft(draft.id, { content: draftBody });
    }
    await product.schedule(draft.id, new Date(timeToSchedule).toISOString());
  }

  return (
    <ProductShell>
      <section className="flex flex-col gap-6">
        <header className="flex flex-wrap items-end justify-between gap-6 pb-2">
          <div className="space-y-3">
            <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-xs font-semibold tracking-wide text-primary shadow-sm">
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              Creation Workspace
            </div>
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent sm:text-5xl">
              Turn signal into a draft
            </h1>
            <p className="max-w-xl text-base text-muted-foreground leading-relaxed">
              Trends, brand voice, and drafts live in one workspace so creation feels directed instead of staring at a blank page.
            </p>
          </div>
          <Sheet open={draftPickerOpen} onOpenChange={setDraftPickerOpen}>
            <SheetTrigger render={<Button type="button" variant="outline" className="gap-2 shrink-0 rounded-xl shadow-sm hover:shadow-md transition-all active:scale-[0.98]" />}>
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
          <div className="relative overflow-hidden rounded-2xl border bg-card/60 p-6 backdrop-blur-2xl shadow-xl transition-all h-fit">
            <div className="absolute inset-x-0 -top-px h-px w-full bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold tracking-tight text-foreground">Prompt Studio</h2>
              <p className="mt-1.5 text-sm text-muted-foreground">Shape your ideas. Pick a platform, tap a trend, or let AI suggest an angle.</p>
            </div>

            <div className="flex flex-col gap-6">
              <Tabs value={platform} onValueChange={setPlatform} className="w-full">
                <TabsList className="grid w-full grid-cols-3 bg-muted/50 p-1">
                  <TabsTrigger value="linkedin" className="rounded-md data-[state=active]:bg-background data-[state=active]:shadow-sm transition-all">LinkedIn</TabsTrigger>
                  <TabsTrigger value="instagram" className="rounded-md data-[state=active]:bg-background data-[state=active]:shadow-sm transition-all">Instagram</TabsTrigger>
                  <TabsTrigger value="twitter" className="rounded-md data-[state=active]:bg-background data-[state=active]:shadow-sm transition-all">X</TabsTrigger>
                </TabsList>
              </Tabs>

              <div className="space-y-3">
                <label className="text-sm font-medium leading-none text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                  What do you want to write about?
                </label>
                <Textarea 
                  value={prompt} 
                  onChange={(event) => setPrompt(event.target.value)} 
                  placeholder="Drop a point of view, a trend, or a half-formed idea..."
                  className="min-h-[140px] resize-none rounded-xl border-border/50 bg-background/50 px-4 py-3 text-sm focus-visible:ring-1 focus-visible:ring-primary/50 transition-all placeholder:text-muted-foreground/60 shadow-sm"
                />
              </div>

              {product.trends?.trends && product.trends.trends.length > 0 && (
                <div className="space-y-2.5">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Trending inspiration</p>
                  <div className="flex flex-wrap gap-2">
                    {product.trends.trends.slice(0, 5).map((trend) => (
                      <button
                        key={trend.topic}
                        className="group relative flex items-center gap-2 rounded-full border border-border/40 bg-background/40 px-3.5 py-1.5 text-[13px] font-medium text-muted-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:bg-background hover:text-foreground active:scale-[0.98]"
                        onClick={() => setPrompt(trend.content_angle)}
                        type="button"
                      >
                        <span className="absolute inset-0 rounded-full opacity-0 ring-1 ring-primary/20 transition-opacity group-hover:opacity-100" />
                        {trend.topic}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-2 flex flex-wrap items-center gap-3 pt-2">
                <Button 
                  type="button"
                  disabled={product.isLoading} 
                  onClick={() => void product.suggest(platform, prompt || undefined)}
                  className="group relative overflow-hidden rounded-xl bg-primary text-primary-foreground shadow-md transition-all hover:shadow-lg active:scale-[0.98] h-10 px-5"
                >
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 opacity-0 transition-opacity group-hover:opacity-100" />
                  {product.isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                  Suggest for me
                </Button>
                <Button 
                  type="button"
                  disabled={locked || !prompt || product.isLoading} 
                  variant="outline" 
                  onClick={() => void product.generate(platform, prompt)}
                  className="rounded-xl border-border bg-background/50 backdrop-blur-sm transition-all hover:bg-muted hover:shadow-sm active:scale-[0.98] h-10 px-5"
                >
                  {product.isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Generate draft
                </Button>
              </div>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-2xl border bg-card/60 p-6 backdrop-blur-2xl shadow-xl transition-all h-fit">
            <div className="absolute inset-x-0 -top-px h-px w-full bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
            
            <div className="mb-6">
              <h2 className="text-xl font-semibold tracking-tight text-foreground">Draft editor</h2>
              <p className="mt-1.5 text-sm text-muted-foreground">
                {draft ? `${(draft.content ?? "").length}/${limit} characters` : "Generated content appears here."}
              </p>
            </div>
            
            <div className="flex flex-col gap-5">
              {product.suggestions.length ? (
                <div className="grid gap-3">
                  {product.suggestions.map((suggestion) => (
                    <button
                      key={suggestion.hook}
                      className="group relative overflow-hidden rounded-xl border border-primary/20 bg-primary/5 p-4 text-left transition-all hover:bg-primary/10 hover:border-primary/40 active:scale-[0.99] shadow-sm"
                      onClick={() => applySuggestion(suggestion)}
                      type="button"
                    >
                      <div className="flex items-start gap-3">
                        <Sparkles className="mt-0.5 h-4 w-4 text-primary shrink-0" />
                        <div>
                          <p className="font-semibold text-primary/90">{suggestion.hook}</p>
                          <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground/90">{suggestion.why_it_works}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : null}

              {draft?.persona_fit_notes?.length ? (
                <div className="rounded-xl border border-secondary/40 bg-secondary/10 px-4 py-3 text-sm shadow-sm backdrop-blur-md transition-all">
                  <div className="flex items-center gap-2 font-semibold text-foreground">
                    <span className="flex h-5 items-center justify-center rounded-full bg-background px-2 text-xs border">
                      {draft.persona_fit_score ?? "N/A"}%
                    </span>
                    Persona Fit
                  </div>
                  <p className="mt-2 text-muted-foreground leading-relaxed">{draft.persona_fit_notes.join(" ")}</p>
                </div>
              ) : null}

              <Textarea
                className="min-h-[320px] resize-y rounded-xl border-border/50 bg-background/50 p-4 text-base leading-relaxed focus-visible:ring-1 focus-visible:ring-primary/50 transition-all shadow-sm placeholder:text-muted-foreground/50"
                value={draftBody}
                onChange={(event) => setDraftBody(event.target.value)}
                placeholder="Your generated draft will appear here..."
              />

              {draft ? (
                <div className="flex flex-col gap-3 rounded-xl border border-border/50 bg-background/40 p-4 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-foreground">Images</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{draft.media?.length ?? 0}/4 attached for LinkedIn or X publishing</p>
                      {draft.platform === "linkedin" && (draft.media?.length ?? 0) > 1 ? (
                        <p className="mt-1 text-xs text-destructive">LinkedIn publishing supports one image in this version.</p>
                      ) : null}
                    </div>
                    <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-border/60 bg-background px-3 py-2 text-xs font-medium shadow-sm transition-all hover:bg-muted active:scale-[0.98]">
                      <ImagePlus size={14} aria-hidden />
                      Add images
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        multiple
                        className="hidden"
                        onChange={(event) => void uploadImages(event.target.files)}
                      />
                    </label>
                  </div>
                  {draft.media?.length ? (
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 pt-2">
                      {draft.media.map((media) => (
                        <div key={media.id} className="relative overflow-hidden rounded-lg border shadow-sm group">
                          {media.preview_url ? (
                            <AuthenticatedImage
                              mediaId={media.id}
                              fallbackSrc={media.preview_url}
                              alt={media.filename}
                              className="aspect-square w-full object-cover transition-transform duration-300 group-hover:scale-105"
                            />
                          ) : (
                            <div className="aspect-square w-full bg-muted animate-pulse" />
                          )}
                          <button
                            type="button"
                            aria-label={`Remove ${media.filename}`}
                            onClick={() => void product.deleteDraftMedia(draft.id, media.id)}
                            className="absolute right-1.5 top-1.5 rounded-md bg-background/90 p-1.5 text-muted-foreground shadow-sm hover:text-destructive hover:bg-background transition-all"
                          >
                            <Trash2 size={13} aria-hidden />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {uploadError ? <p className="text-xs text-destructive">{uploadError}</p> : null}
                </div>
              ) : null}

              {draft ? (
                <div className="rounded-xl border border-border/50 bg-background/40 p-5 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Platform preview</p>
                  <div className="mt-4 rounded-xl border border-border/60 bg-background p-5 shadow-sm">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">{draftBody || "Nothing to preview yet."}</p>
                    {draft.media?.length ? (
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        {draft.media.slice(0, 4).map((media) => (
                          media.preview_url ? (
                            <AuthenticatedImage
                              key={media.id}
                              mediaId={media.id}
                              fallbackSrc={media.preview_url}
                              alt=""
                              className="aspect-video rounded-lg object-cover border"
                            />
                          ) : null
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : null}

              <div className="flex flex-col gap-4 pt-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex flex-wrap items-center gap-3">
                  <Sheet>
                    <SheetTrigger render={<Button type="button" disabled={!draft} variant="outline" className="rounded-xl shadow-sm transition-all hover:bg-muted active:scale-[0.98]" />}>
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
                          <div key={target} className="rounded-xl border p-4 shadow-sm text-sm">
                            <p className="font-semibold capitalize tracking-tight">{target}</p>
                            <p className="mt-3 whitespace-pre-wrap text-muted-foreground leading-relaxed">{content}</p>
                          </div>
                        )) : null}
                      </div>
                    </SheetContent>
                  </Sheet>
                  <Button disabled={!draft || product.isLoading} variant="outline" onClick={() => void saveDraft()} className="rounded-xl shadow-sm transition-all hover:bg-muted active:scale-[0.98]">
                    <Save size={14} aria-hidden className="mr-1.5" />
                    Save
                  </Button>
                  <Button
                    disabled={!draft || product.isLoading}
                    onClick={() => draft && void (async () => {
                      if (draftBody !== (draft.content ?? "")) {
                        await product.updateDraft(draft.id, { content: draftBody });
                      }
                      await product.publish(draft.id);
                    })()}
                    className="rounded-xl shadow-md transition-all active:scale-[0.98]"
                  >
                    Publish now
                  </Button>
                </div>
                
                <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border/60 bg-background/40 p-1 shadow-sm">
                  <input
                    type="datetime-local"
                    value={scheduleAt || tomorrowMorning()}
                    onChange={(event) => setScheduleAt(event.target.value)}
                    className="flex-1 rounded-lg bg-transparent px-3 py-1.5 text-sm outline-none focus:bg-background/80 focus:ring-1 focus:ring-primary/50 transition-all border-none"
                  />
                  <Button disabled={!draft || product.isLoading} variant="outline" onClick={() => void scheduleDraft()} className="rounded-lg shadow-sm transition-all hover:bg-muted active:scale-[0.98] h-[34px] px-3">
                    Schedule
                  </Button>
                </div>
              </div>
              {product.error ? <p className="text-xs font-medium text-destructive mt-1">{product.error}</p> : null}
            </div>
          </div>
        </div>
      </section>
    </ProductShell>
  );
}
