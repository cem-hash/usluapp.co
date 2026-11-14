"""Builds kvkk-aydinlatma.html and acik-riza.html from the app's own legal texts (ios/Uslu/Resources/legal.json),
so the site and the consent screen in Uslu always show the same version.
Run from web/: python3 build_legal.py"""
import html
import json
import os

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, '..', 'ios', 'Uslu', 'Resources', 'legal.json')


def page(title, description, body):
    return f'''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Uslu</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" href="assets/ikon.svg" type="image/svg+xml">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top scrolled">
  <div class="wrap">
    <a class="logo" href="index.html">Uslu</a>
    <nav class="nav"><a class="keep" href="/blog/">Blog</a><a class="keep" href="gizlilik.html">Gizlilik</a></nav>
  </div>
</header>

<main class="page">
{body}
</main>
</body>
</html>
'''


def main():
    t = json.load(open(SRC, encoding='utf-8'))
    c = t['company']

    def fill(s):
        for k in ('name', 'address', 'taxId', 'email'):
            s = s.replace('{company.' + k + '}', c[k])
        return html.escape(s)

    meta = f'<p class="meta">Sürüm {t["version"]} · Son güncelleme {t["date"]}</p>'

    n = t['notice']
    toc = ''.join(f'<li><a href="#b{i + 1}">{html.escape(s["title"])}</a></li>' for i, s in enumerate(n['sections']))
    parts = [f'<h1>{html.escape(n["title"])}</h1>', meta, f'<p>{fill(n["intro"])}</p>',
             f'<div class="box"><p><strong>İçindekiler</strong></p><ol>{toc}</ol></div>']
    for i, s in enumerate(n['sections']):
        parts.append(f'<h2 id="b{i + 1}">{html.escape(s["title"])}</h2>')
        parts += [f'<p>{fill(p)}</p>' for p in s.get('body', [])]
        if s.get('items'):
            parts.append('<ul>' + ''.join(f'<li>{fill(x)}</li>' for x in s['items']) + '</ul>')
    parts.append('<p>Açık rıza verdiğiniz konular için <a href="acik-riza.html">Açık Rıza Metni</a>\'ne, '
                 'uygulamanın genel gizlilik uygulamaları için <a href="gizlilik.html">Gizlilik politikası</a>\'na bakabilirsiniz.</p>')
    parts.append(f'<h2>İletişim</h2><p>{html.escape(c["name"])}<br>{html.escape(c["address"])}<br>'
                 f'<a class="contact" href="mailto:{c["email"]}">{c["email"]}</a></p>')
    open(os.path.join(D, 'kvkk-aydinlatma.html'), 'w', encoding='utf-8').write(
        page(n['title'], 'Uslu: Köpek Eğitimi uygulaması KVKK kapsamında kişisel verilerin işlenmesine ilişkin aydınlatma metni.', '\n'.join(parts)))

    a = t['consent']
    parts = [f'<h1>{html.escape(a["title"])}</h1>', meta, f'<p>{fill(a["intro"])}</p>']
    for item in a['items']:
        parts.append(f'<h2>{html.escape(item["title"])}</h2><p>{fill(item["text"])}</p>')
    parts.append('<div class="box"><p>Açık rıza vermek isteğe bağlıdır. Rızanızı Uslu\'da Ayarlar &gt; Gizlilik ve izinler '
                 f'bölümünden ya da <a href="mailto:{c["email"]}">{c["email"]}</a> adresine yazarak dilediğiniz zaman geri alabilirsiniz. '
                 'Ayrıntılar için <a href="kvkk-aydinlatma.html">Aydınlatma Metni</a>\'ne bakabilirsiniz.</p></div>')
    open(os.path.join(D, 'acik-riza.html'), 'w', encoding='utf-8').write(
        page(a['title'], 'Uslu: Köpek Eğitimi uygulaması açık rıza metni.', '\n'.join(parts)))
    print('kvkk-aydinlatma.html, acik-riza.html')


if __name__ == '__main__':
    main()
