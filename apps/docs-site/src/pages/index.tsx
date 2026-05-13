import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";

export default function Home() {
  return (
    <Layout title="Vecinita Docs" description="Vecinita project documentation">
      <main style={{ maxWidth: 900, margin: "0 auto", padding: "4rem 1rem" }}>
        <h1>Vecinita Documentation</h1>
        <p>
          This site publishes the repository documentation from the top-level docs
          directory and is deployed to GitHub Pages.
        </p>
        <p>
          <Link className="button button--primary button--lg" to="/docs">
            Open Documentation Hub
          </Link>
        </p>
      </main>
    </Layout>
  );
}
