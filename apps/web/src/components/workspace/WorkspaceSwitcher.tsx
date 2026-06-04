"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  ChevronDown,
  Plus,
  Settings,
  Users,
  Briefcase,
  Check,
} from "lucide-react";
import { useWorkspace } from "@/hooks/useWorkspace";
import { Button } from "@/components/ui/Button";

interface WorkspaceSwitcherProps {
  compact?: boolean;
}

export function WorkspaceSwitcher({ compact = false }: WorkspaceSwitcherProps) {
  const {
    workspaces,
    currentWorkspace,
    organizations,
    switchWorkspace,
    isLoading,
  } = useWorkspace();

  const [isOpen, setIsOpen] = useState(false);

  if (workspaces.length <= 1 && organizations.length <= 1) {
    // Single workspace - no switcher needed
    return null;
  }

  const currentOrg = organizations.find(
    (o) => o.id === currentWorkspace?.organization_id
  );

  return (
    <div className="relative">
      {/* Current Workspace Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-3 rounded-xl transition-all duration-200
          ${compact ? "px-3 py-2" : "px-4 py-3 bg-white border border-gray-200 shadow-sm hover:shadow-md"}
        `}
      >
        <div
          className={`
            flex items-center justify-center rounded-lg font-bold text-white
            ${compact ? "w-8 h-8 text-sm" : "w-10 h-10 text-lg"}
          `}
          style={{
            background: currentWorkspace?.brand_colors?.primary
              ? `linear-gradient(135deg, ${currentWorkspace.brand_colors.primary}, ${currentWorkspace.brand_colors.secondary || currentWorkspace.brand_colors.primary})`
              : "linear-gradient(135deg, #6366F1, #8B5CF6)",
          }}
        >
          {currentWorkspace?.client_name?.charAt(0) ||
            currentWorkspace?.name?.charAt(0) ||
            "W"}
        </div>

        {!compact && (
          <div className="flex-1 text-left">
            <p className="font-semibold text-gray-900 text-sm">
              {currentWorkspace?.client_name || currentWorkspace?.name}
            </p>
            <p className="text-xs text-gray-500">
              {currentOrg?.name || currentWorkspace?.organization_name}
            </p>
          </div>
        )}

        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 z-40"
            />

            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-2xl border border-gray-100 z-50 overflow-hidden min-w-[280px]"
            >
              {/* Organizations Section */}
              {organizations.length > 0 && (
                <div className="p-3 border-b border-gray-100">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-2">
                    Organizations
                  </p>
                  {organizations.map((org) => (
                    <div
                      key={org.id}
                      className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                    >
                      <div className="w-6 h-6 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                        <Building2 className="w-3 h-3" />
                      </div>
                      <span className="text-sm font-medium text-gray-700 flex-1">
                        {org.name}
                      </span>
                      {currentWorkspace?.organization_id === org.id && (
                        <Check className="w-4 h-4 text-emerald-500" />
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Workspaces Section */}
              <div className="p-3">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-2">
                  Workspaces
                </p>
                <div className="space-y-1">
                  {workspaces.map((workspace) => (
                    <button
                      key={workspace.id}
                      onClick={() => {
                        switchWorkspace(workspace.id);
                        setIsOpen(false);
                      }}
                      className={`
                        w-full flex items-center gap-3 px-2 py-2.5 rounded-lg transition-colors
                        ${currentWorkspace?.id === workspace.id ? "bg-indigo-50" : "hover:bg-gray-50"}
                      `}
                    >
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                        style={{
                          background: workspace.brand_colors?.primary
                            ? `linear-gradient(135deg, ${workspace.brand_colors.primary}, ${workspace.brand_colors.secondary || workspace.brand_colors.primary})`
                            : "linear-gradient(135deg, #6366F1, #8B5CF6)",
                        }}
                      >
                        {workspace.client_name?.charAt(0) ||
                          workspace.name?.charAt(0) ||
                          "W"}
                      </div>

                      <div className="flex-1 text-left">
                        <p
                          className={`text-sm font-medium ${
                            currentWorkspace?.id === workspace.id
                              ? "text-indigo-900"
                              : "text-gray-700"
                          }`}
                        >
                          {workspace.client_name || workspace.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {workspace.stats?.posts_count || 0} posts ·{" "}
                          {workspace.stats?.competitors_count || 0} competitors
                        </p>
                      </div>

                      {currentWorkspace?.id === workspace.id && (
                        <Check className="w-4 h-4 text-indigo-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="p-3 border-t border-gray-100 space-y-1">
                <button className="w-full flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition-colors">
                  <Plus className="w-4 h-4" />
                  Create Workspace
                </button>
                <button className="w-full flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition-colors">
                  <Settings className="w-4 h-4" />
                  Workspace Settings
                </button>
                <button className="w-full flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition-colors">
                  <Users className="w-4 h-4" />
                  Members
                </button>
                <button className="w-full flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-50 text-sm text-gray-700 transition-colors">
                  <Briefcase className="w-4 h-4" />
                  Organization Settings
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
