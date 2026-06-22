import { useEffect } from "react";

const SITE = "PIAI Teams News";
const DEFAULT_DESC =
  "PIAI Teams News — curated AI papers, tech news, trending repos, and community posts with Korean summaries.";
const OG_IMAGE = "https://jskh-201910840.github.io/teams-news/og-image.png";

interface PageMeta {
  title?: string;
  description?: string;
  url?: string;
}

function setMeta(name: string, content: string, attr: "name" | "property" = "name") {
  let el = document.querySelector(`meta[${attr}="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, name);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

export function usePageMeta({ title, description, url }: PageMeta) {
  useEffect(() => {
    const fullTitle = title ? `${title} · ${SITE}` : SITE;
    document.title = fullTitle;

    const desc = description ?? DEFAULT_DESC;
    setMeta("description", desc);
    setMeta("og:title", fullTitle, "property");
    setMeta("og:description", desc, "property");
    setMeta("og:type", url ? "article" : "website", "property");
    if (url) {
      setMeta("og:url", url, "property");
    }
    setMeta("og:image", OG_IMAGE, "property");
    setMeta("og:image:alt", "포항공대 인공지능연구원 PIAI — PIAI Teams News", "property");
    setMeta("twitter:card", "summary_large_image");
    setMeta("twitter:title", fullTitle);
    setMeta("twitter:description", desc);
    setMeta("twitter:image", OG_IMAGE);
  }, [title, description, url]);
}
