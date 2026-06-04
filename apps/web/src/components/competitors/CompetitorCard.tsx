"use client";

import { motion } from "framer-motion";
import {
  ExternalLink,
  Users,
  TrendingUp,
  MoreHorizontal,
  Trash2,
  BarChart3,
  Target,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/Button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Competitor {
  id: string;
  name: string;
  platform: string;
  handle: string;
  profile_url?: string | null;
  follower_count?: number | null;
  niche_tags?: string[];
  is_active: boolean;
  last_synced_at?: string | null;
  recent_posts_count?: number;
}

interface CompetitorCardProps {
  competitor: Competitor;
  onAnalyze: (id: string) => void;
  onDelete: (id: string) => void;
  isAnalyzing?: boolean;
}

const platformIcons: Record<string, string> = {
  linkedin: "💼",
  twitter: "🐦",
  instagram: "📸",
  facebook: "👥",
};

export function CompetitorCard({
  competitor,
  onAnalyze,
  onDelete,
  isAnalyzing,
}: CompetitorCardProps) {
  const formattedFollowers = competitor.follower_count
    ? competitor.follower_count >= 1000000
      ? `${(competitor.follower_count / 1000000).toFixed(1)}M`
      : competitor.follower_count >= 1000
        ? `${(competitor.follower_count / 1000).toFixed(1)}K`
        : competitor.follower_count.toString()
    : "Unknown";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
      <Card className="p-5 hover:shadow-lg transition-shadow duration-300">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center text-2xl">
              {platformIcons[competitor.platform] || "📊"}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{competitor.name}</h3>
              <a
                href={competitor.profile_url || `#`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                @{competitor.handle}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onAnalyze(competitor.id)}>
                <BarChart3 className="w-4 h-4 mr-2" />
                Analyze Strategy
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete(competitor.id)}
                className="text-red-600"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Remove
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
            <Users className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">Followers</p>
              <p className="font-semibold text-gray-900">{formattedFollowers}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
            <TrendingUp className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">Posts Tracked</p>
              <p className="font-semibold text-gray-900">
                {competitor.recent_posts_count || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Tags */}
        {competitor.niche_tags && competitor.niche_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {competitor.niche_tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium"
              >
                {tag}
              </span>
            ))}
            {competitor.niche_tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                +{competitor.niche_tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Last Sync */}
        <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
          <span>
            Last synced: {" "}
            {competitor.last_synced_at
              ? new Date(competitor.last_synced_at).toLocaleDateString()
              : "Never"}
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => onAnalyze(competitor.id)}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full mr-2"
              />
            ) : (
              <Target className="w-4 h-4 mr-2" />
            )}
            Analyze
          </Button>
        </div>
      </Card>
    </motion.div>
  );
}
