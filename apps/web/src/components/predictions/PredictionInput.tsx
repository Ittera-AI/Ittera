"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Loader2, Hash, AtSign, FileText, Clock } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";

interface PredictionInputProps {
  onAnalyze: (input: {
    content: string;
    platform: string;
    contentType: string;
    hashtags: string[];
    mentions: string[];
  }) => void;
  isLoading: boolean;
}

const PLATFORMS = [
  { id: "linkedin", label: "LinkedIn", icon: "💼" },
  { id: "twitter", label: "Twitter", icon: "🐦" },
  { id: "instagram", label: "Instagram", icon: "📸" },
  { id: "facebook", label: "Facebook", icon: "👥" },
];

const CONTENT_TYPES = [
  { id: "post", label: "Text Post" },
  { id: "article", label: "Article / Long-form" },
  { id: "video", label: "Video Description" },
  { id: "image", label: "Image Caption" },
  { id: "poll", label: "Poll / Question" },
];

export function PredictionInput({ onAnalyze, isLoading }: PredictionInputProps) {
  const [content, setContent] = useState("");
  const [platform, setPlatform] = useState("linkedin");
  const [contentType, setContentType] = useState("post");
  const [hashtags, setHashtags] = useState("");
  const [mentions, setMentions] = useState("");
  const [charCount, setCharCount] = useState(0);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setContent(text);
    setCharCount(text.length);
  };

  const handleSubmit = () => {
    if (!content.trim() || isLoading) return;

    onAnalyze({
      content: content.trim(),
      platform,
      contentType,
      hashtags: hashtags.split(/[,\s]+/).filter(Boolean),
      mentions: mentions.split(/[,\s]+/).filter(Boolean),
    });
  };

  const getPlatformLimit = () => {
    switch (platform) {
      case "twitter":
        return 280;
      case "linkedin":
        return 3000;
      case "instagram":
        return 2200;
      default:
        return 5000;
    }
  };

  const limit = getPlatformLimit();
  const isNearLimit = charCount > limit * 0.9;
  const isOverLimit = charCount > limit;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Platform Selection */}
      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map((p) => (
          <button
            key={p.id}
            onClick={() => setPlatform(p.id)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200
              ${
                platform === p.id
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/25"
                  : "bg-white text-gray-600 border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50"
              }
            `}
          >
            <span>{p.icon}</span>
            <span>{p.label}</span>
          </button>
        ))}
      </div>

      {/* Content Type */}
      <div className="flex flex-wrap gap-2">
        {CONTENT_TYPES.map((type) => (
          <button
            key={type.id}
            onClick={() => setContentType(type.id)}
            className={`
              px-3 py-1.5 rounded-full text-sm transition-all duration-200
              ${
                contentType === type.id
                  ? "bg-gray-900 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }
            `}
          >
            {type.label}
          </button>
        ))}
      </div>

      {/* Content Input */}
      <div className="relative">
        <Textarea
          value={content}
          onChange={handleContentChange}
          placeholder="Paste your content here to get AI predictions for performance, viral potential, and optimal timing..."
          className="min-h-[200px] resize-none pr-20"
        />
        <div className="absolute bottom-3 right-3">
          <span
            className={`text-xs font-medium ${
              isOverLimit
                ? "text-red-500"
                : isNearLimit
                  ? "text-amber-500"
                  : "text-gray-400"
            }`}
          >
            {charCount}/{limit}
          </span>
        </div>
      </div>

      {/* Metadata Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative">
          <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            value={hashtags}
            onChange={(e) => setHashtags(e.target.value)}
            placeholder="Hashtags (comma separated)"
            className="pl-10"
          />
        </div>
        <div className="relative">
          <AtSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            value={mentions}
            onChange={(e) => setMentions(e.target.value)}
            placeholder="Mentions (comma separated)"
            className="pl-10"
          />
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-1.5">
            <FileText className="w-4 h-4" />
            <span>AI will analyze engagement potential</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            <span>Optimal timing recommendation</span>
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!content.trim() || isLoading || isOverLimit}
          size="lg"
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Analyze Content
            </>
          )}
        </Button>
      </div>

      {isOverLimit && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg"
        >
          Content exceeds {platform}&apos;s character limit. Please shorten your content.
        </motion.p>
      )}
    </motion.div>
  );
}
