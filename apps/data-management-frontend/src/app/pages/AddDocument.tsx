import { useState } from "react";
import { ragApi } from "../api/rag-api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Globe, Upload, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router";
import { Switch } from "../components/ui/switch";
import { Slider } from "../components/ui/slider";

type AddDocumentTab = "url" | "upload" | "manual";
type ResourceType = "website" | "document" | "organization" | "dataset" | "service";
type ResourceFormat = "HTML" | "PDF" | "API" | "video" | "TXT" | "DOCX" | "other";

export function AddDocument() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<AddDocumentTab>("url");
  
  // URL Scraping State
  const [url, setUrl] = useState("");
  const [scrapeDepth, setScrapeDepth] = useState(0);
  const [autoTag, setAutoTag] = useState(true);
  const [scraping, setScraping] = useState(false);

  // File Upload State
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Manual Entry State
  const [manualData, setManualData] = useState({
    title: "",
    description: "",
    url: "",
    resource_type: "document" as ResourceType,
    format: "HTML" as ResourceFormat,
    language: "English",
    organization: "",
    content: "",
  });
  const [saving, setSaving] = useState(false);

  const handleScrapeUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) {
      toast.error("Please enter a URL");
      return;
    }

    try {
      setScraping(true);
      const result = await ragApi.scrapeUrl({
        url,
        depth: scrapeDepth,
        auto_tag: autoTag,
      });
      
      toast.success(`Scraping job started! Job ID: ${result.job_id}`);
      toast.info(`Initial job state: ${result.status}`);
      
      // Reset form
      setUrl("");
      setScrapeDepth(0);
      
      // Navigate to scrape jobs page
      setTimeout(() => {
        navigate("/scrape-jobs");
      }, 1500);
    } catch (error) {
      toast.error(`Scraping failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Scraping error:', error);
    } finally {
      setScraping(false);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error("Please select a file");
      return;
    }

    try {
      setUploading(true);
      const result = await ragApi.uploadDocument({
        file,
        auto_tag: autoTag,
      });
      
      toast.success("File uploaded successfully!");
      toast.info(`Document ID: ${result.document_id}`);
      
      // Reset form
      setFile(null);
      
      // Navigate to document detail
      setTimeout(() => {
        navigate(`/document/${result.document_id}`);
      }, 1500);
    } catch (error) {
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleManualCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualData.title || !manualData.description) {
      toast.error("Title and description are required");
      return;
    }

    try {
      setSaving(true);
      const result = await ragApi.createDocument(manualData);
      
      toast.success("Document created successfully!");
      
      // Generate embeddings if content exists
      if (manualData.content) {
        await ragApi.generateEmbeddings(result.id);
        toast.info("Generating embeddings...");
      }
      
      // Navigate to document detail
      setTimeout(() => {
        navigate(`/document/${result.id}`);
      }, 1500);
    } catch (error) {
      toast.error(`Creation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Creation error:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Add to Corpus</h1>
        <p className="text-gray-500 mt-2">
          Add documents to your RAG vector database by scraping URLs, uploading files, or manual entry
        </p>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={(value) => {
          if (value === "url" || value === "upload" || value === "manual") {
            setActiveTab(value);
          }
        }}
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="url">
            <Globe className="w-4 h-4 mr-2" />
            Scrape URL
          </TabsTrigger>
          <TabsTrigger value="upload">
            <Upload className="w-4 h-4 mr-2" />
            Upload File
          </TabsTrigger>
          <TabsTrigger value="manual">
            <FileText className="w-4 h-4 mr-2" />
            Manual Entry
          </TabsTrigger>
        </TabsList>

        {/* URL Scraping Tab */}
        <TabsContent value="url">
          <Card>
            <CardHeader>
              <CardTitle>Scrape Website</CardTitle>
              <CardDescription>
                Provide a URL to scrape and add to your vector database. Configure crawl depth to follow links.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleScrapeUrl} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="url">URL to Scrape *</Label>
                  <Input
                    id="url"
                    type="url"
                    placeholder="https://example.com/page"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="depth">
                    Crawl Depth: {scrapeDepth} {scrapeDepth === 0 ? "(Single page)" : `(Follow ${scrapeDepth} level${scrapeDepth > 1 ? 's' : ''} of links)`}
                  </Label>
                  <Slider
                    id="depth"
                    min={0}
                    max={5}
                    step={1}
                    value={[scrapeDepth]}
                    onValueChange={(value) => setScrapeDepth(value[0])}
                    className="w-full"
                  />
                  <p className="text-sm text-gray-500">
                    Depth 0 scrapes only the provided URL. Higher depths follow links to scrape related pages.
                  </p>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="space-y-0.5">
                    <Label htmlFor="auto-tag">Auto-Tagging</Label>
                    <p className="text-sm text-gray-500">
                      Automatically generate metadata tags using AI
                    </p>
                  </div>
                  <Switch
                    id="auto-tag"
                    checked={autoTag}
                    onCheckedChange={setAutoTag}
                  />
                </div>

                <Button type="submit" disabled={scraping} className="w-full">
                  {scraping ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating Job...
                    </>
                  ) : (
                    <>
                      <Globe className="w-4 h-4 mr-2" />
                      Start Scraping Job
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* File Upload Tab */}
        <TabsContent value="upload">
          <Card>
            <CardHeader>
              <CardTitle>Upload Document</CardTitle>
              <CardDescription>
                Upload PDF, DOCX, TXT, or other document files to add to your corpus
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleFileUpload} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="file">Document File *</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.md"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    required
                  />
                  {file && (
                    <p className="text-sm text-gray-500">
                      Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="space-y-0.5">
                    <Label htmlFor="upload-auto-tag">Auto-Tagging</Label>
                    <p className="text-sm text-gray-500">
                      Automatically generate metadata tags using AI
                    </p>
                  </div>
                  <Switch
                    id="upload-auto-tag"
                    checked={autoTag}
                    onCheckedChange={setAutoTag}
                  />
                </div>

                <Button type="submit" disabled={uploading} className="w-full">
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload Document
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Manual Entry Tab */}
        <TabsContent value="manual">
          <Card>
            <CardHeader>
              <CardTitle>Manual Entry</CardTitle>
              <CardDescription>
                Manually create a document entry with all metadata fields
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleManualCreate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title *</Label>
                    <Input
                      id="title"
                      placeholder="Document title"
                      value={manualData.title}
                      onChange={(e) => setManualData({ ...manualData, title: e.target.value })}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="manual-url">URL</Label>
                    <Input
                      id="manual-url"
                      type="url"
                      placeholder="https://example.com"
                      value={manualData.url}
                      onChange={(e) => setManualData({ ...manualData, url: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description *</Label>
                  <Textarea
                    id="description"
                    placeholder="Brief summary of the document"
                    value={manualData.description}
                    onChange={(e) => setManualData({ ...manualData, description: e.target.value })}
                    rows={3}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="resource_type">Resource Type</Label>
                    <Select
                      value={manualData.resource_type}
                      onValueChange={(value) =>
                        setManualData({
                          ...manualData,
                          resource_type: value as ResourceType,
                        })
                      }
                    >
                      <SelectTrigger id="resource_type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="website">Website</SelectItem>
                        <SelectItem value="document">Document</SelectItem>
                        <SelectItem value="organization">Organization</SelectItem>
                        <SelectItem value="dataset">Dataset</SelectItem>
                        <SelectItem value="service">Service</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="format">Format</Label>
                    <Select
                      value={manualData.format}
                      onValueChange={(value) =>
                        setManualData({
                          ...manualData,
                          format: value as ResourceFormat,
                        })
                      }
                    >
                      <SelectTrigger id="format">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="HTML">HTML</SelectItem>
                        <SelectItem value="PDF">PDF</SelectItem>
                        <SelectItem value="API">API</SelectItem>
                        <SelectItem value="video">Video</SelectItem>
                        <SelectItem value="TXT">TXT</SelectItem>
                        <SelectItem value="DOCX">DOCX</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="language">Language</Label>
                    <Select
                      value={manualData.language}
                      onValueChange={(value) => setManualData({ ...manualData, language: value })}
                    >
                      <SelectTrigger id="language">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="English">English</SelectItem>
                        <SelectItem value="Spanish">Spanish</SelectItem>
                        <SelectItem value="Portuguese">Portuguese</SelectItem>
                        <SelectItem value="French">French</SelectItem>
                        <SelectItem value="German">German</SelectItem>
                        <SelectItem value="Chinese">Chinese</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="organization">Organization</Label>
                    <Input
                      id="organization"
                      placeholder="Provider or owner"
                      value={manualData.organization}
                      onChange={(e) => setManualData({ ...manualData, organization: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="content">Content (Optional)</Label>
                  <Textarea
                    id="content"
                    placeholder="Paste document content here for embedding generation"
                    value={manualData.content}
                    onChange={(e) => setManualData({ ...manualData, content: e.target.value })}
                    rows={6}
                  />
                  <p className="text-sm text-gray-500">
                    If content is provided, embeddings will be generated automatically
                  </p>
                </div>

                <Button type="submit" disabled={saving} className="w-full">
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <FileText className="w-4 h-4 mr-2" />
                      Create Document
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
