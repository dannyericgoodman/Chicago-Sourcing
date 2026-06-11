import type { MetadataRoute } from "next";

// Makes Skim installable to the home screen so it opens fullscreen, like a real app.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Skim",
    short_name: "Skim",
    description: "Your newsletters and blogs, as stories.",
    start_url: "/",
    display: "standalone",
    background_color: "#faf9f7",
    theme_color: "#faf9f7",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
