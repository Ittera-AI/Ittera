"use client";

import { useEffect, useState } from "react";

import { productService } from "@/services/product.service";

type AuthenticatedImageProps = {
  mediaId: string;
  fallbackSrc?: string | null;
  alt: string;
  className?: string;
};

export function AuthenticatedImage({ mediaId, fallbackSrc, alt, className }: AuthenticatedImageProps) {
  const [src, setSrc] = useState<string | null>(fallbackSrc ?? null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    productService
      .mediaPreviewUrl(mediaId)
      .then((url) => {
        objectUrl = url;
        if (active) setSrc(url);
      })
      .catch(() => {
        if (active) setSrc(fallbackSrc ?? null);
      });

    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [fallbackSrc, mediaId]);

  if (!src) {
    return <div className={className} style={{ background: "var(--muted)" }} />;
  }

  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt={alt} className={className} />;
}
