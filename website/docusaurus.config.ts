import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "Vecinita Docs",
  tagline: "Architecture, APIs, testing, and deployment guides",
  favicon: "img/logo.svg",
  url: "https://acadiagit.github.io",
  baseUrl: "/vecinita/",
  organizationName: "acadiagit",
  projectName: "vecinita",
  trailingSlash: false,
  onBrokenLinks: "warn",
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },
  presets: [
    [
      "classic",
      {
        docs: {
          path: "../docs",
          include: ["README.md", "guides/greeting.md"],
          exclude: ["**/INDEX.md"],
          routeBasePath: "docs",
          sidebarPath: "./sidebars.ts",
          editUrl: "https://github.com/acadiagit/vecinita/tree/main/",
        },
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],
  themeConfig: {
    navbar: {
      title: "Vecinita",
      items: [
        {
          type: "docSidebar",
          sidebarId: "docsSidebar",
          position: "left",
          label: "Documentation",
        },
        {
          href: "https://github.com/acadiagit/vecinita",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [{ label: "Documentation Hub", to: "/docs" }],
        },
        {
          title: "Project",
          items: [
            {
              label: "Repository",
              href: "https://github.com/acadiagit/vecinita",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Vecinita`,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
