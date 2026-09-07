---
id: requests-timeouts
source: requests-docs/advanced.md
category: rendimiento
page: 4
---

# Timeouts y reintentos con HTTPAdapter

Por defecto, `requests` no aplica ningún timeout a sus peticiones, lo que puede
hacer que una petición quede colgada indefinidamente si el servidor remoto no
responde. Para evitarlo, se debe pasar siempre el argumento `timeout`, expresado
en segundos, o como una tupla `(timeout_conexion, timeout_lectura)`:

```python
import requests

requests.get("https://api.ejemplo.com/datos", timeout=5)
requests.get("https://api.ejemplo.com/datos", timeout=(3.05, 10))
```

Para configurar reintentos automáticos ante fallos transitorios (por ejemplo,
errores 500 o problemas de conexión), se monta un `HTTPAdapter` con una política
de `Retry` de `urllib3` sobre una `Session`:

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503])
adapter = HTTPAdapter(max_retries=retry_strategy)

session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)
```

Combinar `timeout` con una estrategia de `Retry` es la práctica recomendada para
hacer que un cliente HTTP sea resiliente frente a fallos de red intermitentes.
