---
id: requests-streaming
source: requests-docs/advanced.md
category: rendimiento
page: 6
---

# Descarga de archivos grandes con streaming

Cuando se necesita descargar un archivo grande, no conviene cargar toda la
respuesta en memoria de una sola vez. Para eso, `requests` permite activar el
modo streaming pasando `stream=True` a la petición, lo que evita descargar el
cuerpo completo hasta que se itere sobre él explícitamente:

```python
import requests

with requests.get("https://ejemplo.com/archivo-grande.zip", stream=True) as response:
    response.raise_for_status()
    with open("archivo-grande.zip", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
```

El método `response.iter_content(chunk_size=...)` devuelve el cuerpo de la
respuesta en bloques del tamaño indicado, permitiendo procesarlo o escribirlo a
disco de forma incremental sin agotar la memoria RAM. De forma similar,
`response.iter_lines()` permite iterar línea por línea sobre respuestas de
texto, útil para procesar streams de datos en formato NDJSON o logs en vivo.
