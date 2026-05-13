import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { ragApi, Document, TagSuggestion } from "../api/rag-api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { ArrowLeft, Save, Trash2, Sparkles, Loader2, ExternalLink, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";

export function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [generatingTags, setGeneratingTags] = useState(false);
  const [tagSuggestions, setTagSuggestions] = useState<TagSuggestion[]>([]);
  const [newTag, setNewTag] = useState("");
  const [generatingEmbeddings, setGeneratingEmbeddings] = useState(false);

  const [editedDoc, setEditedDoc] = useState<Partial<Document>>({});

  const loadDocument = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await ragApi.getDocument(id);
      setDocument(data);
      setEditedDoc(data);
    } catch (error) {
      toast.error(`Failed to load document: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Document loading error:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      void loadDocument();
    }
  }, [id, loadDocument]);

  const handleSave = async () => {
    if (!id) return;
    try {
      setSaving(true);
      const updated = await ragApi.updateDocument(id, editedDoc);
      setDocument(updated);
      setEditing(false);
      toast.success("Document updated successfully");
    } catch (error) {
      toast.error(`Failed to save: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Save error:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await ragApi.deleteDocument(id);
      toast.success("Document deleted successfully");
      navigate("/corpus");
    } catch (error) {
      toast.error(`Failed to delete: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Delete error:', error);
    }
  };

  const handleGenerateTags = async () => {
    if (!id) return;
    try {
      setGeneratingTags(true);
      const result = await ragApi.autoGenerateTags(id);
      setTagSuggestions(result.suggestions);
      toast.success(`Generated ${result.suggestions.length} tag suggestions`);
    } catch (error) {
      toast.error(`Failed to generate tags: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Tag generation error:', error);
    } finally {
      setGeneratingTags(false);
    }
  };

  const handleApplySuggestion = async (suggestion: TagSuggestion) => {
    if (!id || !document) return;
    const currentTags = editedDoc.tags || document.tags || [];
    const newTags = [...currentTags, suggestion.tag];
    setEditedDoc({ ...editedDoc, tags: newTags });
    setTagSuggestions(tagSuggestions.filter(s => s.tag !== suggestion.tag));
  };

  const handleAddTag = () => {
    if (!newTag.trim() || !document) return;
    const currentTags = editedDoc.tags || document.tags || [];
    if (currentTags.includes(newTag.trim())) {
      toast.error("Tag already exists");
      return;
    }
    setEditedDoc({ ...editedDoc, tags: [...currentTags, newTag.trim()] });
    setNewTag("");
  };

  const handleRemoveTag = (tag: string) => {
    if (!document) return;
    const currentTags = editedDoc.tags || document.tags || [];
    setEditedDoc({ ...editedDoc, tags: currentTags.filter(t => t !== tag) });
  };

  const handleGenerateEmbeddings = async () => {
    if (!id) return;
    try {
      setGeneratingEmbeddings(true);
      const result = await ragApi.generateEmbeddings(id);
      toast.success(`Generated ${result.vector_count} embeddings`);
      loadDocument(); // Reload to get updated status
    } catch (error) {
      toast.error(`Failed to generate embeddings: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Embedding generation error:', error);
    } finally {
      setGeneratingEmbeddings(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">Document not found</p>
        <Link to="/corpus">
          <Button className="mt-4">Back to Corpus</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <Link to="/corpus">
          <Button variant="ghost">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Corpus
          </Button>
        </Link>
        <div className="flex gap-2">
          {!editing ? (
            <>
              <Button variant="outline" onClick={() => setEditing(true)}>
                Edit
              </Button>
              <Button variant="outline" onClick={loadDocument}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                variant="destructive"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => {
                setEditing(false);
                setEditedDoc(document);
              }}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                {editing ? (
                  <Input
                    id="title"
                    value={editedDoc.title || ""}
                    onChange={(e) => setEditedDoc({ ...editedDoc, title: e.target.value })}
                  />
                ) : (
                  <p className="text-lg font-medium">{document.title}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                {editing ? (
                  <Textarea
                    id="description"
                    value={editedDoc.description || ""}
                    onChange={(e) => setEditedDoc({ ...editedDoc, description: e.target.value })}
                    rows={3}
                  />
                ) : (
                  <p className="text-gray-700">{document.description}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="url">URL</Label>
                {editing ? (
                  <Input
                    id="url"
                    type="url"
                    value={editedDoc.url || ""}
                    onChange={(e) => setEditedDoc({ ...editedDoc, url: e.target.value })}
                  />
                ) : document.url ? (
                  <a
                    href={document.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1"
                  >
                    {document.url}
                    <ExternalLink className="w-4 h-4" />
                  </a>
                ) : (
                  <p className="text-gray-500">No URL</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="resource_type">Resource Type</Label>
                  {editing ? (
                    <Select
                      value={editedDoc.resource_type || document.resource_type}
                      onValueChange={(value) => setEditedDoc({ ...editedDoc, resource_type: value as Document["resource_type"] })}
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
                  ) : (
                    <p className="capitalize">{document.resource_type}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="format">Format</Label>
                  {editing ? (
                    <Select
                      value={editedDoc.format || document.format}
                      onValueChange={(value) => setEditedDoc({ ...editedDoc, format: value as Document["format"] })}
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
                  ) : (
                    <p>{document.format}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  {editing ? (
                    <Select
                      value={editedDoc.language || document.language}
                      onValueChange={(value) => setEditedDoc({ ...editedDoc, language: value })}
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
                  ) : (
                    <p>{document.language}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="organization">Organization</Label>
                  {editing ? (
                    <Input
                      id="organization"
                      value={editedDoc.organization || ""}
                      onChange={(e) => setEditedDoc({ ...editedDoc, organization: e.target.value })}
                    />
                  ) : (
                    <p>{document.organization}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tags Section */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Tags</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerateTags}
                disabled={generatingTags}
              >
                {generatingTags ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Auto-Generate
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Current Tags */}
              <div>
                <Label className="mb-2 block">Current Tags</Label>
                <div className="flex flex-wrap gap-2">
                  {(editing ? (editedDoc.tags || document.tags) : document.tags)?.map((tag, idx) => (
                    <Badge key={idx} variant="secondary" className="flex items-center gap-1">
                      {tag}
                      {editing && (
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-1 hover:text-red-600"
                        >
                          ×
                        </button>
                      )}
                    </Badge>
                  )) || <p className="text-sm text-gray-500">No tags</p>}
                </div>
              </div>

              {/* Add Tag */}
              {editing && (
                <div className="flex gap-2">
                  <Input
                    placeholder="Add new tag"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  />
                  <Button onClick={handleAddTag}>Add</Button>
                </div>
              )}

              {/* Tag Suggestions */}
              {tagSuggestions.length > 0 && (
                <div>
                  <Label className="mb-2 block">Suggestions</Label>
                  <div className="flex flex-wrap gap-2">
                    {tagSuggestions.map((suggestion, idx) => (
                      <Badge
                        key={idx}
                        variant="outline"
                        className="cursor-pointer hover:bg-blue-100"
                        onClick={() => handleApplySuggestion(suggestion)}
                      >
                        {suggestion.tag}
                        <span className="ml-1 text-xs text-gray-500">
                          ({Math.round(suggestion.confidence * 100)}%)
                        </span>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Embedding Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                {document.embedding_status === 'completed' && (
                  <Badge className="bg-green-100 text-green-800">Completed</Badge>
                )}
                {document.embedding_status === 'processing' && (
                  <Badge className="bg-yellow-100 text-yellow-800">Processing</Badge>
                )}
                {document.embedding_status === 'failed' && (
                  <Badge className="bg-red-100 text-red-800">Failed</Badge>
                )}
                {document.embedding_status === 'pending' && (
                  <Badge className="bg-gray-100 text-gray-800">Pending</Badge>
                )}
              </div>
              
              <Button
                variant="outline"
                className="w-full"
                onClick={handleGenerateEmbeddings}
                disabled={generatingEmbeddings}
              >
                {generatingEmbeddings ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Regenerate Embeddings"
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <span className="text-gray-500">ID:</span>
                <p className="font-mono text-xs break-all">{document.id}</p>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <p>{new Date(document.created_at).toLocaleString()}</p>
              </div>
              <div>
                <span className="text-gray-500">Updated:</span>
                <p>{new Date(document.updated_at).toLocaleString()}</p>
              </div>
              {document.scrape_depth !== undefined && (
                <div>
                  <span className="text-gray-500">Scrape Depth:</span>
                  <p>{document.scrape_depth}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete "{document.title}" and its embeddings from the vector database.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
