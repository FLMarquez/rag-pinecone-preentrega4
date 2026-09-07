---
id: requests-auth
source: requests-docs/auth.md
category: seguridad
page: 3
---

# Autenticación HTTP en requests

La librería `requests` incluye soporte integrado para varios esquemas de
autenticación HTTP. Para autenticación básica (HTTP Basic Auth) se utiliza la
clase `requests.auth.HTTPBasicAuth`, que también puede pasarse de forma
abreviada como una tupla `(usuario, password)` al argumento `auth`:

```python
from requests.auth import HTTPBasicAuth
import requests

requests.get("https://api.ejemplo.com/privado", auth=HTTPBasicAuth("user", "pass"))
# equivalente:
requests.get("https://api.ejemplo.com/privado", auth=("user", "pass"))
```

Para autenticación Digest existe `requests.auth.HTTPDigestAuth`, que implementa
el desafío-respuesta definido en el esquema HTTP Digest. Cuando una API requiere
un esquema propio (por ejemplo, firmar la petición con HMAC), se puede crear una
clase de autenticación personalizada heredando de `requests.auth.AuthBase` e
implementando el método `__call__(self, r)`, que recibe el objeto `PreparedRequest`
y debe devolverlo modificado con los encabezados de autenticación necesarios.
