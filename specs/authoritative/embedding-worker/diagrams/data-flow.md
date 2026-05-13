# Data Flow Diagram: Embedding Worker
> Auto-generated: 2026-05-12

## Single Embedding Flow

```mermaid
flowchart LR
    A["User Question<br/>(str)"] -->|"fn.remote(text)"| B["Modal Runtime"]
    B --> C["load_runtime_model()"]
    C --> D["TextEmbedding<br/>(from Volume cache)"]
    D --> E["model.embed([text])"]
    E --> F["ndarray<br/>(384-dim)"]
    F -->|".tolist()"| G["list[float]<br/>(384 elements)"]
    G --> H["dict response<br/>{embedding, model, dimension}"]
    H -->|"Modal return"| I["Gateway"]
    I -->|"INSERT INTO agent.vectors"| J["PostgreSQL"]
```

## Batch Embedding Flow

```mermaid
flowchart LR
    A["Text List<br/>(list[str])"] -->|"fn.remote(texts)"| B["Modal Runtime"]
    B --> C["load_runtime_model()"]
    C --> D["TextEmbedding<br/>(from Volume cache)"]
    D --> E["model.embed(queries)"]
    E --> F["list[ndarray]"]
    F -->|".tolist() each"| G["list[list[float]]"]
    G --> H["dict response<br/>{embeddings, model, dimension}"]
    H -->|"Modal return"| I["Gateway"]
    I -->|"batch INSERT"| J["PostgreSQL"]
```

## Model Loading Flow

```mermaid
flowchart TD
    A["Function invoked"] --> B["load_runtime_model()"]
    B --> C["create_text_embedding()"]
    C --> D{"Model cached<br/>on Volume?"}
    D -->|Yes| E["Load from /models"]
    D -->|No| F["Download from<br/>HuggingFace Hub"]
    F --> G["Save to /models<br/>Volume"]
    G --> E
    E --> H["warmup_embedding_model()"]
    H --> I["model.embed(['warmup'])"]
    I --> J["Model ready"]
```

## Data Transformation

```mermaid
flowchart TD
    A["Input: UTF-8 text<br/>'What housing assistance<br/>programs exist?'"] --> B["Tokenizer<br/>(BAAI/bge-small-en-v1.5)"]
    B --> C["Token IDs<br/>[101, 2054, 3769, ...]"]
    C --> D["Transformer<br/>Forward Pass (CPU)"]
    D --> E["Dense Vector<br/>float32[384]"]
    E --> F["Output: list[float]<br/>[0.0312, -0.0451, 0.0178, ...]"]
```

See: [Data Flow](../06-data-flow.md)
