content = open('src/database.py', encoding='utf-8').read()

old = """        resp = self._session.post(f"{self._url}/v2/pipeline", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        return result["results"][0]["response"]["result"]"""

new = """        resp = self._session.post(f"{self._url}/v2/pipeline", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        r = result["results"][0]
        if r.get("type") == "error":
            raise Exception(r.get("error", {}).get("message", "Turso error"))
        return r.get("response", {}).get("result", {"cols": [], "rows": []})"""

content = content.replace(old, new)
open('src/database.py', 'w', encoding='utf-8').write(content)
print("done")
