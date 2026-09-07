---
id: requests-exceptions
source: requests-docs/exceptions.md
category: manejo-de-errores
page: 5
---

# Manejo de excepciones en requests

La librería `requests` define una jerarquía de excepciones bajo el módulo
`requests.exceptions`, todas ellas heredando de `requests.exceptions.RequestException`.
Las más comunes son:

- `requests.exceptions.ConnectionError`: se lanza cuando no fue posible establecer
  conexión con el servidor (DNS, rechazo de conexión, problemas de red).
- `requests.exceptions.Timeout`: se lanza cuando el servidor no responde dentro
  del tiempo límite indicado en el argumento `timeout`. Incluye las subclases
  `ConnectTimeout` y `ReadTimeout`.
- `requests.exceptions.HTTPError`: se lanza al llamar a `response.raise_for_status()`
  cuando el código de estado HTTP indica un error (4xx o 5xx).
- `requests.exceptions.TooManyRedirects`: se lanza cuando una petición excede el
  número máximo de redirecciones permitidas.

Ejemplo de manejo robusto de errores:

```python
import requests

try:
    response = requests.get("https://api.ejemplo.com/datos", timeout=5)
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("La petición superó el tiempo límite de espera")
except requests.exceptions.ConnectionError:
    print("No se pudo establecer conexión con el servidor")
except requests.exceptions.HTTPError as e:
    print(f"Error HTTP: {e}")
```
