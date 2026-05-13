import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import { Save, Settings as SettingsIcon, Globe, FileText, Database } from "lucide-react";
import { Badge } from "../components/ui/badge";
import {
  getScraperConfigDiagnostic,
  getScraperHealthUrl,
} from "../api/scraper-config";

interface ScrapingConfig {
  // Content Extraction
  content_selector: string;
  strip_boilerplate: boolean;
  normalize_whitespace: boolean;
  
  // Crawling
  follow_links_depth: number;
  allowed_domains: string[];
  max_pages: number;
  
  // Request Settings
  request_timeout: number;
  rate_limit: number;
  user_agent: string;
  deduplicate_content: boolean;
}

interface ProcessingConfig {
  // Chunking
  chunk_size: number;
  chunk_overlap: number;
  min_chunk_length: number;
  max_chunk_length: number;
  split_method: 'paragraph' | 'semantic' | 'sentence' | 'recursive';
  preserve_headers: boolean;
  
  // Embeddings
  embedding_model: string;
  embedding_dimensions: number;
}

interface MetadataConfig {
  // Auto-extraction
  auto_extract_metadata: boolean;
  extract_title: boolean;
  extract_description: boolean;
  extract_author: boolean;
  extract_date: boolean;
  extract_language: boolean;
  
  // Required fields
  required_fields: string[];
  
  // Default values
  default_language: string;
  default_verified: boolean;
}

const DEFAULT_SCRAPING_CONFIG: ScrapingConfig = {
  content_selector: "article, .content, #main, main",
  strip_boilerplate: true,
  normalize_whitespace: true,
  follow_links_depth: 1,
  allowed_domains: [],
  max_pages: 100,
  request_timeout: 30,
  rate_limit: 2,
  user_agent: "RAG-ResourceHub-Bot/1.0",
  deduplicate_content: true,
};

const DEFAULT_PROCESSING_CONFIG: ProcessingConfig = {
  chunk_size: 512,
  chunk_overlap: 100,
  min_chunk_length: 50,
  max_chunk_length: 1000,
  split_method: 'recursive',
  preserve_headers: true,
  embedding_model: 'text-embedding-ada-002',
  embedding_dimensions: 1536,
};

const DEFAULT_METADATA_CONFIG: MetadataConfig = {
  auto_extract_metadata: true,
  extract_title: true,
  extract_description: true,
  extract_author: true,
  extract_date: true,
  extract_language: true,
  required_fields: ['title', 'description', 'url', 'resource_type'],
  default_language: 'English',
  default_verified: false,
};

export function Settings() {
  const [scrapingConfig, setScrapingConfig] = useState<ScrapingConfig>(DEFAULT_SCRAPING_CONFIG);
  const [processingConfig, setProcessingConfig] = useState<ProcessingConfig>(DEFAULT_PROCESSING_CONFIG);
  const [metadataConfig, setMetadataConfig] = useState<MetadataConfig>(DEFAULT_METADATA_CONFIG);
  const [saving, setSaving] = useState(false);
  const [domainsInput, setDomainsInput] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'ok' | 'error'>('idle');
  const [connectionMessage, setConnectionMessage] = useState('');

  const scraperDiagnostic = getScraperConfigDiagnostic();
  const scraperHealthUrl = getScraperHealthUrl();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    // Load from localStorage for demo, in production load from API
    try {
      const stored = localStorage.getItem('rag_settings');
      if (stored) {
        const settings = JSON.parse(stored);
        setScrapingConfig(settings.scraping || DEFAULT_SCRAPING_CONFIG);
        setProcessingConfig(settings.processing || DEFAULT_PROCESSING_CONFIG);
        setMetadataConfig(settings.metadata || DEFAULT_METADATA_CONFIG);
        setDomainsInput((settings.scraping?.allowed_domains || []).join(', '));
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      
      // Parse domains
      const domains = domainsInput
        .split(',')
        .map(d => d.trim())
        .filter(d => d.length > 0);
      
      const updatedScrapingConfig = {
        ...scrapingConfig,
        allowed_domains: domains,
      };

      const settings = {
        scraping: updatedScrapingConfig,
        processing: processingConfig,
        metadata: metadataConfig,
      };

      // Save to localStorage for demo, in production save to API
      localStorage.setItem('rag_settings', JSON.stringify(settings));
      
      // In production, call API:
      // await ragApi.updateSettings(settings);
      
      toast.success("Settings saved successfully");
    } catch (error) {
      toast.error(`Failed to save settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Settings save error:', error);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    setScrapingConfig(DEFAULT_SCRAPING_CONFIG);
    setProcessingConfig(DEFAULT_PROCESSING_CONFIG);
    setMetadataConfig(DEFAULT_METADATA_CONFIG);
    setDomainsInput("");
    toast.info("Settings reset to defaults");
  };

  const testScraperConnection = async () => {
    if (!scraperHealthUrl) {
      setConnectionStatus('error');
      setConnectionMessage('Scraper API URL is missing or invalid.');
      return;
    }

    try {
      setConnectionStatus('testing');
      setConnectionMessage('Testing connectivity and warming up backend if needed...');

      const maxAttempts = 5;
      let lastMessage = 'No response from scraper health endpoint.';

      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => {
          controller.abort();
        }, 8000);

        setConnectionMessage(
          attempt === 1
            ? 'Testing connectivity...'
            : `Warming scraper backend (attempt ${attempt}/${maxAttempts})...`,
        );

        try {
          const response = await fetch(scraperHealthUrl, {
            method: 'GET',
            signal: controller.signal,
          });

          if (response.ok) {
            setConnectionStatus('ok');
            setConnectionMessage(
              attempt === 1
                ? 'Scraper API health check succeeded.'
                : 'Scraper API health check succeeded after warmup.',
            );
            return;
          }

          lastMessage = `Health endpoint returned ${response.status} ${response.statusText}`;
        } catch (error) {
          lastMessage = error instanceof Error ? error.message : 'Connection test failed';
        } finally {
          window.clearTimeout(timeoutId);
        }

        if (attempt < maxAttempts) {
          await new Promise((resolve) => {
            setTimeout(resolve, 1500);
          });
        }
      }

      setConnectionStatus('error');
      setConnectionMessage(`Scraper API still unavailable after warmup attempts: ${lastMessage}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Connection test failed';
      setConnectionStatus('error');
      setConnectionMessage(message);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <SettingsIcon className="w-8 h-8 text-gray-700" />
            Configuration Settings
          </h1>
          <p className="text-gray-500 mt-2">Configure scraping, processing, and metadata extraction parameters</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={resetToDefaults}>
            Reset to Defaults
          </Button>
          <Button onClick={saveSettings} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="scraping" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Scraper Runtime Connectivity</CardTitle>
            <CardDescription>
              Validate browser-to-scraper connectivity and inspect runtime config diagnostics.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={scraperDiagnostic.issues.length > 0 ? 'destructive' : 'default'}>
                {scraperDiagnostic.issues.length > 0 ? 'Config Issue' : 'Config OK'}
              </Badge>
              <Badge variant="secondary">
                Auth Mode: Direct API Key Bearer
              </Badge>
            </div>

            <div className="text-sm text-gray-600 space-y-1">
              <p>Configured Base URL: {scraperDiagnostic.apiBaseUrl || 'Not set'}</p>
              <p>Health URL: {scraperHealthUrl || 'Unavailable until config is valid'}</p>
            </div>

            {scraperDiagnostic.issues.length > 0 && (
              <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                {scraperDiagnostic.issues.join(' | ')}
              </div>
            )}

            {scraperDiagnostic.warnings.length > 0 && (
              <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-900">
                {scraperDiagnostic.warnings.join(' | ')}
              </div>
            )}

            {connectionStatus !== 'idle' && (
              <div
                className={
                  connectionStatus === 'ok'
                    ? 'rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900'
                    : connectionStatus === 'testing'
                      ? 'rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700'
                      : 'rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900'
                }
              >
                {connectionMessage}
              </div>
            )}

            <Button
              variant="outline"
              disabled={connectionStatus === 'testing' || !scraperHealthUrl}
              onClick={testScraperConnection}
            >
              {connectionStatus === 'testing' ? 'Testing Connection...' : 'Test Scraper Connection'}
            </Button>
          </CardContent>
        </Card>

        <TabsList>
          <TabsTrigger value="scraping">
            <Globe className="w-4 h-4 mr-2" />
            Scraping
          </TabsTrigger>
          <TabsTrigger value="processing">
            <FileText className="w-4 h-4 mr-2" />
            Processing
          </TabsTrigger>
          <TabsTrigger value="metadata">
            <Database className="w-4 h-4 mr-2" />
            Metadata
          </TabsTrigger>
        </TabsList>

        {/* Scraping Configuration */}
        <TabsContent value="scraping" className="space-y-6">
          {/* Content Extraction */}
          <Card>
            <CardHeader>
              <CardTitle>Content Extraction</CardTitle>
              <CardDescription>Control what text to extract and how to clean it</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="content_selector">Content Selector</Label>
                <Input
                  id="content_selector"
                  value={scrapingConfig.content_selector}
                  onChange={(e) => setScrapingConfig({ ...scrapingConfig, content_selector: e.target.value })}
                  placeholder="article, .content, #main"
                />
                <p className="text-sm text-gray-500">
                  CSS selectors for main content (comma-separated). Tools: <Badge variant="secondary">trafilatura</Badge> <Badge variant="secondary">readability-lxml</Badge>
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Strip Boilerplate</Label>
                  <p className="text-sm text-gray-500">Remove navigation, ads, and footer content</p>
                </div>
                <Switch
                  checked={scrapingConfig.strip_boilerplate}
                  onCheckedChange={(checked) => setScrapingConfig({ ...scrapingConfig, strip_boilerplate: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Normalize Whitespace</Label>
                  <p className="text-sm text-gray-500">Clean up formatting and extra spaces</p>
                </div>
                <Switch
                  checked={scrapingConfig.normalize_whitespace}
                  onCheckedChange={(checked) => setScrapingConfig({ ...scrapingConfig, normalize_whitespace: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Deduplicate Content</Label>
                  <p className="text-sm text-gray-500">Remove duplicate pages during crawl</p>
                </div>
                <Switch
                  checked={scrapingConfig.deduplicate_content}
                  onCheckedChange={(checked) => setScrapingConfig({ ...scrapingConfig, deduplicate_content: checked })}
                />
              </div>
            </CardContent>
          </Card>

          {/* Crawling Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Crawling Settings</CardTitle>
              <CardDescription>Control crawl depth and scope</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="follow_links_depth">Follow Links Depth</Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="follow_links_depth"
                    type="number"
                    min="0"
                    max="5"
                    value={scrapingConfig.follow_links_depth}
                    onChange={(e) => setScrapingConfig({ ...scrapingConfig, follow_links_depth: parseInt(e.target.value) || 0 })}
                    className="w-24"
                  />
                  <div className="flex gap-2">
                    {[0, 1, 2, 3].map(depth => (
                      <Button
                        key={depth}
                        variant={scrapingConfig.follow_links_depth === depth ? "default" : "outline"}
                        size="sm"
                        onClick={() => setScrapingConfig({ ...scrapingConfig, follow_links_depth: depth })}
                      >
                        {depth}
                      </Button>
                    ))}
                  </div>
                </div>
                <p className="text-sm text-gray-500">
                  0 = single page, 1 = page + links, 2-3 = follow links recursively (typical: 0-3)
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_pages">Max Pages</Label>
                <Input
                  id="max_pages"
                  type="number"
                  min="1"
                  max="10000"
                  value={scrapingConfig.max_pages}
                  onChange={(e) => setScrapingConfig({ ...scrapingConfig, max_pages: parseInt(e.target.value) || 100 })}
                />
                <p className="text-sm text-gray-500">Maximum pages to crawl (typical: 100-10000)</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="allowed_domains">Allowed Domains</Label>
                <Input
                  id="allowed_domains"
                  value={domainsInput}
                  onChange={(e) => setDomainsInput(e.target.value)}
                  placeholder="example.org, example.com"
                />
                <p className="text-sm text-gray-500">
                  Comma-separated domains to restrict crawl scope (leave empty for no restriction)
                </p>
                {domainsInput && (
                  <div className="flex gap-2 flex-wrap mt-2">
                    {domainsInput.split(',').map((domain, idx) => (
                      <Badge key={idx} variant="secondary">{domain.trim()}</Badge>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Request Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Request Settings</CardTitle>
              <CardDescription>Configure request behavior and rate limiting</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="request_timeout">Request Timeout (seconds)</Label>
                <Input
                  id="request_timeout"
                  type="number"
                  min="5"
                  max="120"
                  value={scrapingConfig.request_timeout}
                  onChange={(e) => setScrapingConfig({ ...scrapingConfig, request_timeout: parseInt(e.target.value) || 30 })}
                />
                <p className="text-sm text-gray-500">Prevent stuck requests (typical: 10-30s)</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="rate_limit">Rate Limit (requests/second)</Label>
                <Input
                  id="rate_limit"
                  type="number"
                  min="0.1"
                  max="10"
                  step="0.1"
                  value={scrapingConfig.rate_limit}
                  onChange={(e) => setScrapingConfig({ ...scrapingConfig, rate_limit: parseFloat(e.target.value) || 1 })}
                />
                <p className="text-sm text-gray-500">
                  Avoid getting banned (typical: 1-5 req/sec). Use <Badge variant="secondary">playwright</Badge> for JS-heavy sites
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="user_agent">User Agent</Label>
                <Input
                  id="user_agent"
                  value={scrapingConfig.user_agent}
                  onChange={(e) => setScrapingConfig({ ...scrapingConfig, user_agent: e.target.value })}
                  placeholder="RAG-ResourceHub-Bot/1.0"
                />
                <p className="text-sm text-gray-500">Identify your crawler to website owners</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Processing Configuration */}
        <TabsContent value="processing" className="space-y-6">
          {/* Chunking Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Text Chunking</CardTitle>
              <CardDescription>Control how text becomes RAG chunks for embeddings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="chunk_size">Chunk Size (tokens)</Label>
                <Input
                  id="chunk_size"
                  type="number"
                  min="100"
                  max="2000"
                  value={processingConfig.chunk_size}
                  onChange={(e) => setProcessingConfig({ ...processingConfig, chunk_size: parseInt(e.target.value) || 512 })}
                />
                <p className="text-sm text-gray-500">Tokens per chunk (typical: 300-800)</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="chunk_overlap">Chunk Overlap (tokens)</Label>
                <Input
                  id="chunk_overlap"
                  type="number"
                  min="0"
                  max="500"
                  value={processingConfig.chunk_overlap}
                  onChange={(e) => setProcessingConfig({ ...processingConfig, chunk_overlap: parseInt(e.target.value) || 100 })}
                />
                <p className="text-sm text-gray-500">Overlap between chunks to preserve context (typical: 50-150)</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="min_chunk_length">Min Chunk Length</Label>
                  <Input
                    id="min_chunk_length"
                    type="number"
                    min="10"
                    max="500"
                    value={processingConfig.min_chunk_length}
                    onChange={(e) => setProcessingConfig({ ...processingConfig, min_chunk_length: parseInt(e.target.value) || 50 })}
                  />
                  <p className="text-sm text-gray-500">Skip tiny fragments (50-100)</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="max_chunk_length">Max Chunk Length</Label>
                  <Input
                    id="max_chunk_length"
                    type="number"
                    min="500"
                    max="5000"
                    value={processingConfig.max_chunk_length}
                    onChange={(e) => setProcessingConfig({ ...processingConfig, max_chunk_length: parseInt(e.target.value) || 1000 })}
                  />
                  <p className="text-sm text-gray-500">Avoid huge chunks (1000)</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="split_method">Split Method</Label>
                <Select
                  value={processingConfig.split_method}
                  onValueChange={(value) =>
                    setProcessingConfig({
                      ...processingConfig,
                      split_method: value as ProcessingConfig['split_method'],
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recursive">Recursive (section → paragraph → sentence)</SelectItem>
                    <SelectItem value="semantic">Semantic (uses embeddings to detect topic breaks)</SelectItem>
                    <SelectItem value="paragraph">Paragraph-based</SelectItem>
                    <SelectItem value="sentence">Sentence-based</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500">How splitting works. Recursive is most common.</p>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Preserve Headers</Label>
                  <p className="text-sm text-gray-500">Keep section headers for better context</p>
                </div>
                <Switch
                  checked={processingConfig.preserve_headers}
                  onCheckedChange={(checked) => setProcessingConfig({ ...processingConfig, preserve_headers: checked })}
                />
              </div>
            </CardContent>
          </Card>

          {/* Embedding Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Embedding Configuration</CardTitle>
              <CardDescription>Configure the embedding model and parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="embedding_model">Embedding Model</Label>
                <Select
                  value={processingConfig.embedding_model}
                  onValueChange={(value) => setProcessingConfig({ ...processingConfig, embedding_model: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text-embedding-ada-002">OpenAI: text-embedding-ada-002 (1536 dims)</SelectItem>
                    <SelectItem value="text-embedding-3-small">OpenAI: text-embedding-3-small (1536 dims)</SelectItem>
                    <SelectItem value="text-embedding-3-large">OpenAI: text-embedding-3-large (3072 dims)</SelectItem>
                    <SelectItem value="all-MiniLM-L6-v2">Open Source: all-MiniLM-L6-v2 (384 dims)</SelectItem>
                    <SelectItem value="all-mpnet-base-v2">Open Source: all-mpnet-base-v2 (768 dims)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-gray-500">
                  Choose your embedding model. OpenAI models require API key.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="embedding_dimensions">Embedding Dimensions</Label>
                <Input
                  id="embedding_dimensions"
                  type="number"
                  value={processingConfig.embedding_dimensions}
                  onChange={(e) => setProcessingConfig({ ...processingConfig, embedding_dimensions: parseInt(e.target.value) || 1536 })}
                  disabled
                />
                <p className="text-sm text-gray-500">Automatically set based on model selection</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metadata Configuration */}
        <TabsContent value="metadata" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Metadata Extraction</CardTitle>
              <CardDescription>Configure automatic metadata extraction from documents</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Auto-Extract Metadata</Label>
                  <p className="text-sm text-gray-500">Automatically extract metadata from documents</p>
                </div>
                <Switch
                  checked={metadataConfig.auto_extract_metadata}
                  onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, auto_extract_metadata: checked })}
                />
              </div>

              <div className="border-t pt-4 space-y-4">
                <h4 className="font-medium text-sm">Extract Fields</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Title</Label>
                    <Switch
                      checked={metadataConfig.extract_title}
                      onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, extract_title: checked })}
                      disabled={!metadataConfig.auto_extract_metadata}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Description</Label>
                    <Switch
                      checked={metadataConfig.extract_description}
                      onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, extract_description: checked })}
                      disabled={!metadataConfig.auto_extract_metadata}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Author</Label>
                    <Switch
                      checked={metadataConfig.extract_author}
                      onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, extract_author: checked })}
                      disabled={!metadataConfig.auto_extract_metadata}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Publication Date</Label>
                    <Switch
                      checked={metadataConfig.extract_date}
                      onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, extract_date: checked })}
                      disabled={!metadataConfig.auto_extract_metadata}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label className="text-sm">Language</Label>
                    <Switch
                      checked={metadataConfig.extract_language}
                      onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, extract_language: checked })}
                      disabled={!metadataConfig.auto_extract_metadata}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Important Metadata Fields</CardTitle>
              <CardDescription>These fields dramatically improve retrieval accuracy</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-2">Core Fields</h4>
                  <ul className="space-y-1 text-sm text-gray-600">
                    <li>• <Badge variant="secondary">title</Badge> - improves ranking</li>
                    <li>• <Badge variant="secondary">url</Badge> - traceability</li>
                    <li>• <Badge variant="secondary">category</Badge> - filtering</li>
                    <li>• <Badge variant="secondary">organization</Badge> - entity search</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">Enhanced Fields</h4>
                  <ul className="space-y-1 text-sm text-gray-600">
                    <li>• <Badge variant="secondary">location</Badge> - geographic filtering</li>
                    <li>• <Badge variant="secondary">language</Badge> - multilingual support</li>
                    <li>• <Badge variant="secondary">document_type</Badge> - policy/guide/service</li>
                    <li>• <Badge variant="secondary">date_published</Badge> - freshness ranking</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Default Values</CardTitle>
              <CardDescription>Default values for new documents</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="default_language">Default Language</Label>
                <Select
                  value={metadataConfig.default_language}
                  onValueChange={(value) => setMetadataConfig({ ...metadataConfig, default_language: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="English">English</SelectItem>
                    <SelectItem value="Spanish">Spanish</SelectItem>
                    <SelectItem value="Portuguese">Portuguese</SelectItem>
                    <SelectItem value="French">French</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Default Verified Status</Label>
                  <p className="text-sm text-gray-500">New documents are marked as verified by default</p>
                </div>
                <Switch
                  checked={metadataConfig.default_verified}
                  onCheckedChange={(checked) => setMetadataConfig({ ...metadataConfig, default_verified: checked })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
