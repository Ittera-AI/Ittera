"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Target, BarChart3, AlertCircle } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/Button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { CompetitorCard } from "@/components/competitors/CompetitorCard";
import { GapAnalysis } from "@/components/competitors/GapAnalysis";
import { useCompetitors } from "@/hooks/useCompetitors";
import { AddCompetitorDialog } from "@/components/competitors/AddCompetitorDialog";

export default function CompetitorsPage() {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);

  const {
    competitors,
    gapAnalysis,
    isLoading,
    isAnalyzing,
    error,
    addCompetitor,
    analyzeStrategy,
    analyzeGaps,
  } = useCompetitors();

  const handleAnalyze = async (id: string) => {
    setAnalyzingId(id);
    try {
      await analyzeStrategy(id);
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleCreateContent = (topic: string) => {
    // Navigate to content generation with this topic
    window.location.href = `/content?topic=${encodeURIComponent(topic)}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-amber-50/20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                  <Target className="w-5 h-5 text-white" />
                </div>
                Competitive Intelligence
              </h1>
              <p className="mt-1 text-gray-500">
                Track competitors, analyze strategies, and identify content gaps
              </p>
            </div>

            <Button
              onClick={() => setShowAddDialog(true)}
              className="bg-gradient-to-r from-amber-500 to-orange-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Competitor
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-50 border border-red-100 rounded-lg flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-red-600">{error}</p>
          </motion.div>
        )}

        <Tabs defaultValue="competitors" className="space-y-6">
          <TabsList className="bg-white border border-gray-200">
            <TabsTrigger value="competitors" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              Competitors
            </TabsTrigger>
            <TabsTrigger value="gaps" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Content Gaps
            </TabsTrigger>
          </TabsList>

          <TabsContent value="competitors" className="space-y-6">
            {competitors.length === 0 && !isLoading ? (
              <Card className="p-12 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-100 flex items-center justify-center">
                  <Target className="w-8 h-8 text-amber-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No competitors tracked yet
                </h3>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  Add your first competitor to start analyzing their content strategy
                  and identifying opportunities.
                </p>
                <Button onClick={() => setShowAddDialog(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add First Competitor
                </Button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {competitors.map((competitor) => (
                  <CompetitorCard
                    key={competitor.id}
                    competitor={competitor}
                    onAnalyze={handleAnalyze}
                    onDelete={() => {}}
                    isAnalyzing={analyzingId === competitor.id}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="gaps" className="space-y-6">
            {!gapAnalysis ? (
              <Card className="p-12 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-indigo-100 flex items-center justify-center">
                  <BarChart3 className="w-8 h-8 text-indigo-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Run Gap Analysis
                </h3>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  Analyze the content gaps between you and your competitors to discover
                  new opportunities.
                </p>
                <Button
                  onClick={analyzeGaps}
                  disabled={isAnalyzing || competitors.length === 0}
                  className="bg-gradient-to-r from-indigo-500 to-purple-600"
                >
                  {isAnalyzing ? (
                    <>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"
                      />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Analyze Gaps
                    </>
                  )}
                </Button>
              </Card>
            ) : (
              <GapAnalysis
                data={gapAnalysis}
                onCreateContent={handleCreateContent}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Add Competitor Dialog */}
      <AddCompetitorDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        onAdd={addCompetitor}
      />
    </div>
  );
}
