"use client";

import { useState, useEffect, useCallback } from "react";
import { brainService } from "@/services/brain-service";
import { useBrainStore } from "@/store/brain-store";
import { getErrorMessage } from "@/lib/api-client";
import type { Brain, BrainCreate, BrainDocument } from "@/types";

/** Hook for listing, creating, and deleting brains. */
export function useBrains() {
  const [brains, setBrains] = useState<Brain[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { selectedBrain, setSelectedBrain } = useBrainStore();

  const fetchBrains = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await brainService.list();
      setBrains(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBrains();
  }, [fetchBrains]);

  const createBrain = async (payload: BrainCreate): Promise<Brain | null> => {
    try {
      const brain = await brainService.create(payload);
      setBrains((prev) => [...prev, brain]);
      setSelectedBrain(brain);
      return brain;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    }
  };

  const deleteBrain = async (brainId: string): Promise<void> => {
    try {
      await brainService.remove(brainId);
      setBrains((prev: Brain[]) => prev.filter((b: Brain) => b.id !== brainId));
      if (selectedBrain?.id === brainId) {
        setSelectedBrain(null);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return { brains, isLoading, error, selectedBrain, setSelectedBrain, createBrain, deleteBrain, refetch: fetchBrains };
}

/** Hook for managing documents connected to a specific brain. */
export function useBrainDocuments(brainId: string | null) {
  const [documents, setDocuments] = useState<BrainDocument[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async () => {
    if (!brainId) { setDocuments([]); return; }
    setIsLoading(true);
    setError(null);
    try {
      const data = await brainService.listDocuments(brainId);
      setDocuments(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [brainId]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const addDocument = async (documentId: string): Promise<void> => {
    if (!brainId) return;
    try {
      await brainService.addDocument(brainId, documentId);
      await fetchDocuments();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const removeDocument = async (documentId: string): Promise<void> => {
    if (!brainId) return;
    try {
      await brainService.removeDocument(brainId, documentId);
      setDocuments((prev: BrainDocument[]) => prev.filter((d: BrainDocument) => d.id !== documentId));
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return { documents, isLoading, error, addDocument, removeDocument, refetch: fetchDocuments };
}
