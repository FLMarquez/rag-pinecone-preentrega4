# Pre-entrega 4: Sistema RAG escalable en la nube con Pinecone

Módulo de recuperación escalable que implementa un flujo RAG completo sobre
Pinecone Serverless: ingesta con metadatos avanzados, recuperador híbrido
(vectorial + BM25) y evaluación con Precision@k / Recall@k.

Dataset de ejemplo: documentación técnica (en español) sobre la librería
Python `requests` — 6 documentos Markdown en [data/documents/](data/documents/),
cada uno con frontmatter de metadatos (`id`, `source`, `category`, `page`).

## Estructura del repositorio

```
.
├── data/
│   ├── documents/          # Documentos fuente (Markdown con frontmatter)
│   └── golden_set.json     # Preguntas de evaluación con documento esperado
├── src/
│   ├── config.py            # Variables de entorno y configuración
│   ├── document_loader.py   # Carga .md / .json / .pdf a Document normalizados
│   ├── setup_pinecone.py    # Crea el índice Serverless si no existe
│   ├── ingest.py             # Chunking + embeddings + upsert a Pinecone
│   ├── hybrid_retriever.py   # Clase RAGSystem (EnsembleRetriever BM25+vector)
│   └── evaluate.py           # Cálculo de Precision@5 y Recall@5
├── requirements.txt
├── .env.example
└── README.md
```

## 1. Setup del entorno

Requiere **Python 3.10–3.13**. Algunas dependencias del ecosistema LangChain
(en particular `langchain-pinecone`) todavía no publican wheels para
**Python 3.14** — si tu `python` por defecto es 3.14, `pip install` va a
fallar con un error del estilo:

```
ERROR: Could not find a version that satisfies the requirement langchain-pinecone>=0.2.0
```

Si te pasa esto, no es necesario desinstalar Python 3.14: alcanza con crear
el entorno virtual apuntando a una versión compatible (3.11, 3.12 o 3.13) que
tengas instalada en paralelo.

```bash
# Windows: fijate qué versiones de Python tenés instaladas
py -0

# Creá el venv con una versión compatible (ejemplo: 3.13)
py -3.13 -m venv .venv          # Windows
# python3.13 -m venv .venv      # macOS/Linux

.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# Completar en .env: PINECONE_API_KEY, GOOGLE_API_KEY, INDEX_NAME
```

> Recordá activar el entorno (`.venv\Scripts\activate` en Windows) en **cada
> terminal nueva** que abras antes de correr los comandos `python -m src....`
> — si no, van a usar el Python global del sistema (y potencialmente la
> versión incompatible) en lugar del `.venv`.

Necesitás una cuenta de [Pinecone](https://www.pinecone.io/) (plan gratuito
alcanza para un índice Serverless) y una API key de Google AI Studio
(https://aistudio.google.com/apikey) para generar embeddings con Gemini
(`models/gemini-embedding-001`, truncado a 768 dimensiones vía
`output_dimensionality` para mantener el tamaño de índice).

> **Windows:** si ves caracteres corruptos en tildes/ñ en la consola, corré
> con `set PYTHONIOENCODING=utf-8` (cmd) o `$env:PYTHONIOENCODING="utf-8"`
> (PowerShell) antes de los comandos `python -m src....`.

## 2. Crear el índice de Pinecone (replicar la infraestructura)

El índice se crea automáticamente al correr la ingesta, pero también podés
crearlo (o verificarlo) de forma explícita:

```bash
python -m src.setup_pinecone
```

Esto:
- Se conecta a Pinecone con `PINECONE_API_KEY`.
- Revisa si ya existe un índice llamado `INDEX_NAME`.
- Si no existe, crea un índice **Serverless** (`cloud=aws`, `region=us-east-1`
  por defecto, configurable en `.env`) con `dimension=768` y `metric=cosine`,
  consistente con `models/gemini-embedding-001` de Gemini (truncado a 768 con
  `output_dimensionality`).

> **Mismatch de dimensiones:** si cambiás el modelo de embeddings, actualizá
> `EMBEDDING_DIMENSION` en `.env` *antes* de crear el índice. Pinecone no
> permite reindexar con otra dimensión sin recrear el índice.

## 3. Pipeline de ingesta

```bash
python -m src.ingest
```

Qué hace:
1. Carga los documentos de `data/documents/` (Markdown con frontmatter; también
   soporta `.json` y `.pdf` vía `document_loader.py`).
2. Divide cada documento en chunks con `RecursiveCharacterTextSplitter`
   (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100` caracteres — un punto medio para no
   perder contexto semántico ni diluir la precisión del embedding).
3. Genera embeddings con `GoogleGenerativeAIEmbeddings` (`models/gemini-embedding-001`,
   truncado a 768 dimensiones).
4. Sube los vectores a Pinecone con `PineconeVectorStore.add_texts`, usando el
   **namespace** `requests-docs` (configurable) para mantener la búsqueda
   acotada y evitar ruido si en el futuro se agregan otros tipos de datos al
   mismo índice.
5. Guarda en la metadata de cada vector: `id`, `parent_id` (id del documento
   original), `source`, `category`, `page`, `chunk_index` y **`text`** (el
   contenido del chunk). Guardar el texto en la metadata evita tener que
   consultar una base de datos relacional aparte para mostrar el contenido
   recuperado.

## 4. Recuperador híbrido (`RAGSystem`)

`src/hybrid_retriever.py` define la clase `RAGSystem`, que encapsula un
`EnsembleRetriever` de LangChain combinando:

- **BM25Retriever** (búsqueda léxica) — reconstruye el mismo corpus de chunks
  usado en la ingesta para búsquedas exactas por términos técnicos, nombres de
  clases (`HTTPAdapter`, `HTTPBasicAuth`) o palabras clave poco frecuentes en
  el espacio semántico.
- **PineconeVectorStore retriever** (búsqueda vectorial) — similitud semántica
  sobre los embeddings almacenados en Pinecone, dentro del namespace
  configurado.

```python
from src.hybrid_retriever import RAGSystem

rag = RAGSystem(top_k=5, bm25_weight=0.4, vector_weight=0.6)
resultados = rag.query("¿Cómo configuro un timeout en requests?")
for doc in resultados:
    print(doc.metadata["parent_id"], doc.page_content[:100])
```

`RAGSystem.query(pregunta, k=5)` devuelve los top-k documentos combinando
ambos rankings vía `EnsembleRetriever`.

## 5. Generación de respuestas (RAG completo)

`src/generate.py` cierra el pipeline: toma los documentos recuperados por
`RAGSystem` y le pide a Gemini (`gemini-3.5-flash-lite` por defecto,
configurable vía `GENERATION_MODEL`) que redacte una respuesta en lenguaje
natural citando el `id` de cada fuente usada, sin apoyarse en conocimiento
fuera del contexto recuperado. Llama a la API REST de Gemini directamente
con `requests` (con reintentos ante timeouts) en vez de usar el SDK
`google-genai`, que en algunas redes resultó lento/inestable para generación
de texto.

```bash
python -m src.generate "¿Cómo configuro un timeout en requests?"
```

```python
from src.generate import answer

print(answer("¿Cómo configuro un timeout en requests?"))
```

## 6. Evaluación (Precision@5 y Recall@5)

`data/golden_set.json` define 5 preguntas con su documento fuente esperado
(`documento_id_esperado`, referenciando el `id` de un archivo en
`data/documents/`).

```bash
python -m src.evaluate
```

Por cada pregunta se recuperan los top-5 documentos y se calcula:

- **Recall@5**: 1 si el documento esperado aparece entre los 5 recuperados,
  0 si no (hay un único documento relevante por pregunta).
- **Precision@5**: proporción de los 5 documentos recuperados que coinciden
  con el documento relevante esperado.

El script imprime un detalle por pregunta y un resumen final con los
promedios. Los valores reales dependen de tus embeddings/índice — ejecutá
`python -m src.evaluate` para tu propio reporte. Como referencia, esta es la
salida obtenida corriendo solo la mitad léxica (BM25) del retriever híbrido
sobre las 5 preguntas del golden set (sin componente vectorial, que requiere
credenciales reales de Pinecone/Google):

```
=== Evaluación del RAGSystem (Golden Set) ===

[OK ] ¿Cómo se configura un timeout personalizado para evitar que una petición HTTP quede colgada indefinidamente?
       esperado:   requests-timeouts
       recuperados: ['requests-timeouts', 'requests-basics', 'requests-session', 'requests-auth', 'requests-timeouts']
       precision@5: 0.40   recall@5: 1.00

[OK ] ¿Qué clase de requests se usa para autenticación HTTP Basic Auth?
       esperado:   requests-auth
       recuperados: ['requests-auth', 'requests-auth', 'requests-basics', 'requests-exceptions', 'requests-basics']
       precision@5: 0.40   recall@5: 1.00

[OK ] ¿Cómo se reutiliza la conexión TCP entre múltiples peticiones al mismo servidor para mejorar el rendimiento?
       esperado:   requests-session
       recuperados: ['requests-session', 'requests-exceptions', 'requests-basics', 'requests-auth', 'requests-timeouts']
       precision@5: 0.20   recall@5: 1.00

[OK ] ¿Qué excepción lanza requests cuando el servidor no responde dentro del tiempo límite configurado?
       esperado:   requests-exceptions
       recuperados: ['requests-exceptions', 'requests-exceptions', 'requests-timeouts', 'requests-basics', 'requests-streaming']
       precision@5: 0.40   recall@5: 1.00

[OK ] ¿Cómo se descarga un archivo grande sin cargarlo completo en memoria RAM?
       esperado:   requests-streaming
       recuperados: ['requests-streaming', 'requests-streaming', 'requests-basics', 'requests-session', 'requests-basics']
       precision@5: 0.40   recall@5: 1.00

--- Resumen ---
Precision@5 promedio: 0.36
Recall@5 promedio:    1.00
```

El golden set fue diseñado para que cada pregunta apunte, sin ambigüedad, a un
único documento fuente; por eso el componente léxico ya alcanza Recall@5 = 1.00
por sí solo. Sumar el componente vectorial (Pinecone) aporta robustez cuando
las preguntas usan sinónimos o paráfrasis que BM25 no matchea por coincidencia
exacta de términos.

## Decisiones de diseño / errores evitados

- **Dimensión del índice**: fijada en 768, truncando `models/gemini-embedding-001`
  de Gemini vía `output_dimensionality` (configurable vía `.env` si se cambia
  de modelo).
- **Namespace**: todos los vectores de este dataset se suben al namespace
  `requests-docs`, evitando mezclar búsquedas con otros tipos de datos que
  pudieran convivir en el mismo índice.
- **Chunking**: 800 caracteres con 100 de overlap — suficiente para mantener
  contexto semántico en explicaciones técnicas sin diluir la precisión del
  embedding con chunks demasiado largos.
- **Metadata rica**: cada vector guarda `text`, `source`, `category`, `page`
  y `parent_id`, permitiendo mostrar resultados y trazar la fuente original
  sin una base de datos relacional adicional.
