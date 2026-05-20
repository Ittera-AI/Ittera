"use client";

import { useProductStore } from "@/stores/product.store";

export function useProduct() {
  return useProductStore();
}
