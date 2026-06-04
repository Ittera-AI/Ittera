"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Plus, Globe, Target } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AddCompetitorDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (data: {
    name: string;
    platform: string;
    handle: string;
    profile_url?: string;
    niche_tags?: string[];
  }) => Promise<unknown>;
}

const PLATFORMS = [
  { id: "linkedin", label: "LinkedIn", icon: "💼" },
  { id: "twitter", label: "Twitter", icon: "🐦" },
  { id: "instagram", label: "Instagram", icon: "📸" },
  { id: "facebook", label: "Facebook", icon: "👥" },
];

export function AddCompetitorDialog({ open, onClose, onAdd }: AddCompetitorDialogProps) {
  const [name, setName] = useState("");
  const [platform, setPlatform] = useState("linkedin");
  const [handle, setHandle] = useState("");
  const [profileUrl, setProfileUrl] = useState("");
  const [nicheTags, setNicheTags] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim() || !handle.trim()) {
      setError("Please fill in all required fields");
      return;
    }

    setIsSubmitting(true);
    try {
      await onAdd({
        name: name.trim(),
        platform,
        handle: handle.trim().replace(/^@/, ""),
        profile_url: profileUrl.trim() || undefined,
        niche_tags: nicheTags.split(/[,;]+/).map((t) => t.trim()).filter(Boolean),
      });

      // Reset and close
      setName("");
      setHandle("");
      setProfileUrl("");
      setNicheTags("");
      onClose();
    } catch {
      setError("Failed to add competitor. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
          >
            <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                    <Target className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-gray-900">Add Competitor</h2>
                    <p className="text-sm text-gray-500">
                      Track and analyze competitor content
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="p-6 space-y-5">
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600"
                  >
                    {error}
                  </motion.div>
                )}

                {/* Platform Selection */}
                <div>
                  <Label className="text-sm font-medium text-gray-700 mb-2 block">
                    Platform
                  </Label>
                  <div className="grid grid-cols-4 gap-2">
                    {PLATFORMS.map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setPlatform(p.id)}
                        className={`
                          flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all
                          ${
                            platform === p.id
                              ? "border-amber-500 bg-amber-50"
                              : "border-gray-200 hover:border-gray-300"
                          }
                        `}
                      >
                        <span className="text-2xl">{p.icon}</span>
                        <span className="text-xs font-medium text-gray-700">
                          {p.label}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Name */}
                <div>
                  <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                    Competitor Name *
                  </Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., HubSpot"
                    className="mt-1"
                    required
                  />
                </div>

                {/* Handle */}
                <div>
                  <Label htmlFor="handle" className="text-sm font-medium text-gray-700">
                    Username/Handle *
                  </Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 font-medium">
                      @
                    </span>
                    <Input
                      id="handle"
                      value={handle}
                      onChange={(e) => setHandle(e.target.value)}
                      placeholder="hubspot"
                      className="pl-8"
                      required
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Without the @ symbol
                  </p>
                </div>

                {/* Profile URL */}
                <div>
                  <Label htmlFor="url" className="text-sm font-medium text-gray-700">
                    Profile URL (optional)
                  </Label>
                  <div className="relative mt-1">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      id="url"
                      value={profileUrl}
                      onChange={(e) => setProfileUrl(e.target.value)}
                      placeholder="https://linkedin.com/company/hubspot"
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Niche Tags */}
                <div>
                  <Label htmlFor="tags" className="text-sm font-medium text-gray-700">
                    Niche Tags (optional)
                  </Label>
                  <Input
                    id="tags"
                    value={nicheTags}
                    onChange={(e) => setNicheTags(e.target.value)}
                    placeholder="Marketing, SaaS, B2B (comma separated)"
                    className="mt-1"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onClose}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 bg-gradient-to-r from-amber-500 to-orange-600"
                  >
                    {isSubmitting ? (
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"
                      />
                    ) : (
                      <Plus className="w-4 h-4 mr-2" />
                    )}
                    Add Competitor
                  </Button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
