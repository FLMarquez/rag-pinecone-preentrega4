---
id: requests-basics
source: requests-docs/quickstart.md
category: fundamentos
page: 1
---

# Peticiones básicas con la librería requests

La librería `requests` de Python permite realizar peticiones HTTP de forma sencilla.
Para hacer una petición GET se utiliza `requests.get(url)`, que devuelve un objeto
`Response`. Este objeto expone `response.status_code` con el código HTTP recibido,
`response.text` con el cuerpo como cadena de texto y `response.json()` para decodificar
automáticamente una respuesta en formato JSON.

Para enviar datos en una petición POST se usa `requests.post(url, data=payload)` cuando
se envía un formulario, o `requests.post(url, json=payload)` cuando se envía un cuerpo
JSON. Los parámetros de la URL (query string) se pasan mediante el argumento `params`,
por ejemplo `requests.get(url, params={"q": "python"})`.

Los encabezados personalizados se agregan con el argumento `headers`, un diccionario de
pares clave-valor. Por ejemplo, para enviar un token en el encabezado `Authorization`:

```python
import requests

response = requests.get(
    "https://api.ejemplo.com/datos",
    headers={"Authorization": "Bearer TOKEN"},
)
print(response.status_code, response.json())
```

Es una buena práctica revisar siempre `response.status_code` o llamar a
`response.raise_for_status()` antes de procesar el contenido de la respuesta.
