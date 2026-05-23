"use client"

import { useState } from "react"
import { api, PersonaProfile } from "@/lib/api"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/Button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Loader2 } from "lucide-react"

export function PersonaResults({ persona, onConfirm }: { persona: PersonaProfile; onConfirm: () => void }) {
  const [profile, setProfile] = useState<PersonaProfile>(persona)
  const [isSaving, setIsSaving] = useState(false)

  const handleUpdate = (field: keyof PersonaProfile, value: any) => {
    setProfile({ ...profile, [field]: value })
  }

  const handleSaveAndConfirm = async () => {
    setIsSaving(true)
    try {
      await api.persona.update({
        persona_summary: profile.persona_summary,
        niche: profile.niche,
        target_audience: profile.target_audience,
        voice_tone: profile.voice_tone,
        positioning: profile.positioning,
        content_pillars: typeof profile.content_pillars === "string" ? (profile.content_pillars as string).split("\n") : profile.content_pillars,
        audience_pain_points: typeof profile.audience_pain_points === "string" ? (profile.audience_pain_points as string).split("\n") : profile.audience_pain_points,
      })
      await api.persona.confirm()
      onConfirm()
    } catch (err: any) {
      alert("Failed to confirm persona: " + err.message)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Your Content Persona</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Review and tweak the insights Ittera extracted. These will drive your content strategy.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Persona Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea 
              rows={4}
              value={profile.persona_summary || ""} 
              onChange={(e) => handleUpdate("persona_summary", e.target.value)} 
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Voice & Tone</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea 
              rows={4}
              value={profile.voice_tone || ""} 
              onChange={(e) => handleUpdate("voice_tone", e.target.value)} 
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Positioning</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea 
              rows={4}
              value={profile.positioning || ""} 
              onChange={(e) => handleUpdate("positioning", e.target.value)} 
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Niche & Audience</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Niche</Label>
              <Input 
                value={profile.niche || ""} 
                onChange={(e) => handleUpdate("niche", e.target.value)} 
              />
            </div>
            <div>
              <Label>Target Audience</Label>
              <Input 
                value={profile.target_audience || ""} 
                onChange={(e) => handleUpdate("target_audience", e.target.value)} 
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Content Pillars</CardTitle>
            <CardDescription>One per line</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              rows={5}
              value={Array.isArray(profile.content_pillars) ? profile.content_pillars.join("\n") : profile.content_pillars} 
              onChange={(e) => handleUpdate("content_pillars", e.target.value)} 
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audience Pain Points</CardTitle>
            <CardDescription>One per line</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea 
              rows={5}
              value={Array.isArray(profile.audience_pain_points) ? profile.audience_pain_points.join("\n") : profile.audience_pain_points} 
              onChange={(e) => handleUpdate("audience_pain_points", e.target.value)} 
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSaveAndConfirm} disabled={isSaving} size="lg">
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Confirm and continue
        </Button>
      </div>
    </div>
  )
}
