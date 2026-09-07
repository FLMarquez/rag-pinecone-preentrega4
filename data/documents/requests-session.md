---
id: requests-session
source: requests-docs/advanced.md
category: rendimiento
page: 2
---

# Objetos Session y reutilización de conexiones

Cuando se realizan múltiples peticiones al mismo host, conviene usar un objeto
`requests.Session()` en lugar de llamar directamente a `requests.get()` o
`requests.post()` cada vez. Un `Session` reutiliza la conexión TCP subyacente
gracias al *connection pooling* de `urllib3`, lo que reduce la latencia al evitar
el costo de abrir un nuevo handshake TCP/TLS en cada petición.

Además, un `Session` persiste automáticamente las cookies entre peticiones y
permite configurar valores por defecto (headers, autenticación, proxies) que se
aplican a todas las peticiones realizadas con esa instancia:

```python
import requests

with requests.Session() as session:
    session.headers.update({"User-Agent": "mi-app/1.0"})
    session.get("https://api.ejemplo.com/login")
    respuesta = session.get("https://api.ejemplo.com/datos")
```

Usar `Session` es especialmente recomendable en aplicaciones que hacen muchas
llamadas a la misma API, ya que mejora notablemente el rendimiento comparado con
crear una conexión nueva en cada llamada individual.
