"""Parse a cached tirepressure.com '<year>-<make>-<model>-tire-pressure' page into (size, trims, row_text)."""
import html, re
def rows(path):
    t = open(path, errors="replace").read()
    body = t[t.find("Tire Inflation Chart"):]
    body = body[:body.find("</table>")]
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) == 4 and re.match(r"^(P|LT)?\d{3}/\d{2}Z?R\d{2}|^\d{2}x", cells[0]):
            out.append({"size": cells[0], "front": cells[1], "rear": cells[2], "trims": cells[3], "text": " ".join(cells)})
    return out
