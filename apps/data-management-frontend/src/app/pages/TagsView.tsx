import { useCallback, useEffect, useState } from "react";
import { ragApi } from "../api/rag-api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Search, Tag, Filter, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router";
import { useLocale } from "../i18n/LocaleContext";

interface TagStats {
  tag: string;
  label: string;
  count: number;
  category?: string;
}

const TAG_CATEGORIES = {
  topic: ["housing", "healthcare", "food-assistance", "legal-aid", "immigration", "employment",
          "education", "childcare", "transportation", "financial-assistance", "mental-health"],
  audience: ["immigrants", "seniors", "veterans", "children", "youth", "adults", "low-income"],
  geography: ["statewide", "Providence", "Providence County", "Rhode Island"],
  access: ["free", "appointment-required", "application-required", "wheelchair-accessible"],
} as const;

function getCategoryForTag(tag: string): string {
  for (const [category, tags] of Object.entries(TAG_CATEGORIES)) {
    if (tags.some(t => tag.toLowerCase().includes(t.toLowerCase()) || t.toLowerCase().includes(tag.toLowerCase()))) {
      return category;
    }
  }
  return 'custom';
}

export function TagsView() {
  const { locale, t } = useLocale();
  const [allTags, setAllTags] = useState<TagStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const loadTags = useCallback(async () => {
    try {
      setLoading(true);
      const data = await ragApi.getAllTags(locale);
      const tagStats: TagStats[] = (data.tags || []).map((row) => ({
        tag: row.tag,
        label: row.label || row.tag,
        count: row.resource_count ?? row.source_count ?? data.tag_counts[row.tag] ?? 0,
        category: getCategoryForTag(row.tag),
      }));
      tagStats.sort((a, b) => b.count - a.count);
      setAllTags(tagStats);
    } catch (error) {
      toast.error(`Failed to load tags: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Tags loading error:', error);
    } finally {
      setLoading(false);
    }
  }, [locale]);

  useEffect(() => {
    void loadTags();
  }, [loadTags]);

  const filteredTags = allTags.filter(tagStat => {
    const normalizedQuery = searchQuery.toLowerCase();
    if (
      searchQuery &&
      !tagStat.tag.toLowerCase().includes(normalizedQuery) &&
      !tagStat.label.toLowerCase().includes(normalizedQuery)
    ) {
      return false;
    }
    if (selectedCategory !== 'all' && tagStat.category !== selectedCategory) {
      return false;
    }
    return true;
  });

  const tagsByCategory = {
    topic: filteredTags.filter(t => t.category === 'topic'),
    audience: filteredTags.filter(t => t.category === 'audience'),
    geography: filteredTags.filter(t => t.category === 'geography'),
    access: filteredTags.filter(t => t.category === 'access'),
    custom: filteredTags.filter(t => t.category === 'custom'),
  };

  const totalDocuments = allTags.reduce((sum, t) => sum + t.count, 0);
  const uniqueTags = allTags.length;
  const avgTagsPerDoc = totalDocuments / (uniqueTags || 1);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t('tags.title')}</h1>
        <p className="text-gray-500 mt-2">{t('tags.subtitle')}</p>
      </div>

      <Card className="mb-6 border-blue-200 bg-blue-50/70">
        <CardContent className="pt-6 text-sm text-blue-950 space-y-2">
          <p>{t('tags.disclosureTopics')}</p>
          <p>{t('tags.disclosureResources')}</p>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              {t('tags.uniqueTags')}
            </CardTitle>
            <Tag className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{uniqueTags}</div>
            <p className="text-xs text-gray-500 mt-1">{t('tags.subtitle')}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              {t('tags.totalUsage')}
            </CardTitle>
            <TrendingUp className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDocuments}</div>
            <p className="text-xs text-gray-500 mt-1">{t('tags.totalUsage')}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              {t('tags.avgPerDocument')}
            </CardTitle>
            <Filter className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgTagsPerDoc.toFixed(1)}</div>
            <p className="text-xs text-gray-500 mt-1">{t('tags.avgPerDocument')}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search & Filter */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <Input
                placeholder={t('tags.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={selectedCategory === 'all' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('all')}
              >
                {t('tags.all')}
              </Button>
              <Button
                variant={selectedCategory === 'topic' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('topic')}
              >
                {t('tags.topic')}
              </Button>
              <Button
                variant={selectedCategory === 'audience' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('audience')}
              >
                {t('tags.audience')}
              </Button>
              <Button
                variant={selectedCategory === 'geography' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('geography')}
              >
                {t('tags.geography')}
              </Button>
              <Button
                variant={selectedCategory === 'access' ? 'default' : 'outline'}
                onClick={() => setSelectedCategory('access')}
              >
                {t('tags.access')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tags Display */}
      <Tabs defaultValue="all" className="space-y-6">
        <TabsList>
          <TabsTrigger value="all">{t('tags.all')} ({filteredTags.length})</TabsTrigger>
          <TabsTrigger value="topic">{t('tags.topic')} ({tagsByCategory.topic.length})</TabsTrigger>
          <TabsTrigger value="audience">{t('tags.audience')} ({tagsByCategory.audience.length})</TabsTrigger>
          <TabsTrigger value="geography">{t('tags.geography')} ({tagsByCategory.geography.length})</TabsTrigger>
          <TabsTrigger value="access">{t('tags.access')} ({tagsByCategory.access.length})</TabsTrigger>
          <TabsTrigger value="custom">{t('tags.custom')} ({tagsByCategory.custom.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <TagGrid tags={filteredTags} loading={loading} />
        </TabsContent>

        <TabsContent value="topic">
          <TagGrid tags={tagsByCategory.topic} loading={loading} category="topic" />
        </TabsContent>

        <TabsContent value="audience">
          <TagGrid tags={tagsByCategory.audience} loading={loading} category="audience" />
        </TabsContent>

        <TabsContent value="geography">
          <TagGrid tags={tagsByCategory.geography} loading={loading} category="geography" />
        </TabsContent>

        <TabsContent value="access">
          <TagGrid tags={tagsByCategory.access} loading={loading} category="access" />
        </TabsContent>

        <TabsContent value="custom">
          <TagGrid tags={tagsByCategory.custom} loading={loading} category="custom" />
        </TabsContent>
      </Tabs>

      {/* Metadata Schema Reference */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>{t('tags.schemaTitle')}</CardTitle>
          <CardDescription>{t('tags.schemaDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                {t('tags.topicCategory')}
              </h3>
              <div className="flex flex-wrap gap-2">
                {TAG_CATEGORIES.topic.map(tag => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                {t('tags.audience')}
              </h3>
              <div className="flex flex-wrap gap-2">
                {TAG_CATEGORIES.audience.map(tag => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                {t('tags.geography')}
              </h3>
              <div className="flex flex-wrap gap-2">
                {TAG_CATEGORIES.geography.map(tag => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                {t('tags.access')}
              </h3>
              <div className="flex flex-wrap gap-2">
                {TAG_CATEGORIES.access.map(tag => (
                  <Badge key={tag} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface TagGridProps {
  tags: TagStats[];
  loading: boolean;
  category?: string;
}

function TagGrid({ tags, loading, category }: TagGridProps) {
  const { t } = useLocale();

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
          <div key={i} className="animate-pulse">
            <div className="h-24 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  if (tags.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Tag className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">
            {category ? t('tags.emptyCategory', { category }) : t('tags.empty')}
          </p>
        </CardContent>
      </Card>
    );
  }

  const getCategoryColor = (cat?: string) => {
    switch (cat) {
      case 'topic': return 'bg-blue-100 border-blue-300 hover:bg-blue-200';
      case 'audience': return 'bg-green-100 border-green-300 hover:bg-green-200';
      case 'geography': return 'bg-purple-100 border-purple-300 hover:bg-purple-200';
      case 'access': return 'bg-orange-100 border-orange-300 hover:bg-orange-200';
      default: return 'bg-gray-100 border-gray-300 hover:bg-gray-200';
    }
  };

  const getCategoryLabel = (cat?: string) => {
    switch (cat) {
      case 'topic': return t('tags.topic');
      case 'audience': return t('tags.audience');
      case 'geography': return t('tags.geography');
      case 'access': return t('tags.access');
      default: return t('tags.custom');
    }
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {tags.map((tagStat) => (
        <Link
          key={tagStat.tag}
          to={`/corpus?search=${encodeURIComponent(tagStat.tag)}`}
        >
          <Card className={`cursor-pointer transition-all ${getCategoryColor(tagStat.category)} border-2`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <Tag className="w-4 h-4 text-gray-600" />
                <Badge variant="outline" className="text-xs">
                  {tagStat.count}
                </Badge>
              </div>
              <h3 className="font-medium text-gray-900 truncate" title={tagStat.tag}>
                {tagStat.label}
              </h3>
              {tagStat.label !== tagStat.tag && (
                <p className="text-xs text-gray-500 mt-1 truncate" title={tagStat.tag}>
                  {tagStat.tag}
                </p>
              )}
              {tagStat.category && (
                <p className="text-xs text-gray-500 mt-1 capitalize">
                  {getCategoryLabel(tagStat.category)}
                </p>
              )}
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
