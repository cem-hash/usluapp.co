"""Builds usluapp.co/blog from blog-src/*.md: article pages, blog and category indexes, OG images, sitemap.xml,
robots.txt, RSS, llms.txt and llms-full.txt. Static HTML only, so search engines and AI crawlers read everything
without running JavaScript. Run from anywhere: python3 web/build_blog.py [--no-og]"""
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys

import markdown
import yaml

WEB = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(WEB, 'blog-src')
OUT = os.path.join(WEB, 'blog')
SITE = 'https://usluapp.co'
APP_ID = '6826392423'
# Flip to True when Uslu is live on the App Store: buttons then link to the store and Safari shows the smart banner.
APP_LIVE = False
APP_URL = f'https://apps.apple.com/tr/app/id{APP_ID}' if APP_LIVE else f'{SITE}/#indir'
APP_CTA = "App Store'dan indir" if APP_LIVE else "Kasımda App Store'da"
SKIP = {'YAZIM-REHBERI.md', 'KONULAR.md'}

CATS = {
    'temel': ('Temel eğitim', '#FFE3A2', 'odul'),
    'tuvalet': ('Tuvalet eğitimi', '#CFE8FF', 'pati_izi'),
    'davranis': ('Davranış sorunları', '#FAD4CF', 'soru'),
    'yavru': ('Yavru köpek', '#DDF3E5', 'top'),
    'bilim': ('Bilim ne diyor', '#E6DEFA', 'parilti'),
    'yasam': ('Birlikte yaşam', '#FCE6C8', 'kalp'),
}
# Fıstık's pose per category (web/assets/fistik), so pages next to each other do not repeat the same dog
POSES = {'temel': 'fistik_pati_veriyor_sag', 'tuvalet': 'fistik_oturuyor_sag', 'davranis': 'fistik_onden_oturuyor_bas_egik',
         'yavru': 'fistik_oyun_daveti_sol', 'bilim': 'fistik_onden_oturuyor_mutlu', 'yasam': 'fistik_uyuyor_sag'}


def dog(pose, cls):
    return f'<div class="{cls}" aria-hidden="true"><img src="/assets/fistik/{pose}.svg" alt="" width="300" height="300"></div>'
TR = str.maketrans('çğıöşüâîûÇĞİÖŞÜÂÎÛ', 'cgiosuaiuCGIOSUAIU')
MONTHS = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']


def slugify(text):
    s = text.translate(TR).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'bolum'


def esc(s):
    return html.escape(str(s), quote=True)


def tr_date(d):
    return f'{d.day} {MONTHS[d.month - 1]} {d.year}'


def load_posts():
    posts = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith('.md') or name in SKIP:
            continue
        raw = open(os.path.join(SRC, name), encoding='utf-8').read()
        m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
        if not m:
            print('skip (no frontmatter):', name)
            continue
        meta = yaml.safe_load(m.group(1))
        body = m.group(2).strip()
        meta['slug'] = meta.get('slug') or name[:-3]
        d = meta.get('date') or dt.date.today()
        meta['date'] = d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d))
        meta['body_md'] = body
        meta['words'] = len(re.findall(r'\w+', body))
        meta['minutes'] = max(3, round(meta['words'] / 200))
        meta.setdefault('category', 'temel')
        meta.setdefault('faq', [])
        meta.setdefault('sources', [])
        meta.setdefault('keywords', [])
        posts.append(meta)
    # newest first, then by order of the topics list
    order = {}
    konular = open(os.path.join(SRC, 'KONULAR.md'), encoding='utf-8').read()
    for i, slug in enumerate(re.findall(r'^\| \d+ \| ([a-z0-9-]+) \|', konular, re.M)):
        order[slug] = i
    posts.sort(key=lambda p: (-p['date'].toordinal(), order.get(p['slug'], 99)))
    return posts


def render_body(md_text):
    """Markdown to HTML with Turkish heading ids; returns (html, [(id, title)]) for the table of contents."""
    out = markdown.markdown(md_text, extensions=['tables', 'sane_lists', 'attr_list'])
    toc, seen = [], set()

    def h2(m):
        title = re.sub('<[^>]+>', '', m.group(1))
        hid = slugify(title)
        while hid in seen:
            hid += '-2'
        seen.add(hid)
        toc.append((hid, title))
        return f'<h2 id="{hid}">{m.group(1)}</h2>'
    out = re.sub(r'<h2>(.*?)</h2>', h2, out)
    out = re.sub(r'<h3>(.*?)</h3>', lambda m: f'<h3 id="{slugify(re.sub("<[^>]+>", "", m.group(1)))}">{m.group(1)}</h3>', out)
    out = out.replace('<table>', '<div class="table"><table>').replace('</table>', '</table></div>')
    # outbound links open in a new tab and carry no referrer weight
    out = re.sub(r'<a href="(https?://[^"]+)">', r'<a href="\1" target="_blank" rel="noopener">', out)
    return out, toc


def source_link(text):
    m = re.search(r'(https?://\S+)', text)
    if not m:
        return esc(text)
    url = m.group(1).rstrip('.,;)')
    label = text.replace(m.group(1), '').strip(' .·')
    return f'{esc(label)} <a href="{esc(url)}" target="_blank" rel="noopener">{esc(url.replace("https://", ""))}</a>'


# ------------------------------------------------------------------ shared page parts



def head(title, desc, canonical, og_image, extra='', og_type='website'):
    smart = f'<meta name="apple-itunes-app" content="app-id={APP_ID}">' if APP_LIVE else ''
    return f'''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Uslu">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFE3A2">
{smart}
<link rel="icon" href="/assets/ikon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="Uslu Blog" href="{SITE}/blog/feed.xml">
<link rel="preload" href="/assets/fonts/InstrumentSerif-Regular.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/style.css">
<link rel="stylesheet" href="/blog/blog.css">
{extra}
</head>
<body>
<div class="progress" aria-hidden="true"></div>
<header class="top" id="top">
  <div class="wrap">
    <a class="logo" href="/">Uslu</a>
    <nav class="nav">
      <a href="/#ozellikler">Özellikler</a>
      <a class="keep" href="/blog/">Blog</a>
      <a href="/destek.html">Destek</a>
      <a class="keep btn mini" href="{APP_URL}">{APP_CTA}</a>
    </nav>
  </div>
</header>
'''


def foot(posts):
    cats = ''.join(f'<a href="/blog/kategori/{k}/">{v[0]}</a>' for k, v in CATS.items())
    return f'''
<footer>
  <div class="wrap">
    <span>© {dt.date.today().year} Protrom Yazılım ve Ticaret A.Ş.</span>
    <nav>
      <a href="/">Ana sayfa</a>
      <a href="/blog/">Blog</a>
      {cats}
      <a href="/gizlilik.html">Gizlilik</a>
      <a href="/destek.html">Destek</a>
    </nav>
  </div>
</footer>
<div class="dock" id="dock" hidden>
  <img src="/assets/ikon.svg" alt="" width="40" height="40">
  <div><b>Uslu: Köpek Eğitimi</b><span>Köpeğine özel plan, ödülle kısa dersler</span></div>
  <a class="btn mini" href="{APP_URL}">{APP_CTA}</a>
  <button type="button" aria-label="Kapat" onclick="this.parentElement.remove();try{{sessionStorage.setItem('dock','0')}}catch(e){{}}">×</button>
</div>
<script>
(function () {{
  var d = document.documentElement; d.classList.add('js');
  var top = document.getElementById('top'), dock = document.getElementById('dock'), bar = document.querySelector('.progress');
  var hidden = false; try {{ hidden = sessionStorage.getItem('dock') === '0'; }} catch (e) {{}}
  function onScroll() {{
    var y = window.scrollY, h = d.scrollHeight - innerHeight;
    if (top) top.classList.toggle('scrolled', y > 8);
    if (bar) bar.style.transform = 'scaleX(' + (h > 0 ? Math.min(1, y / h) : 0) + ')';
    if (dock && !hidden) dock.hidden = y < innerHeight * 0.9;
  }}
  // anything that has reached the screen, or was jumped past, is shown; nothing can stay hidden above the reader
  var pending = [].slice.call(document.querySelectorAll('.reveal')), ticking = false;
  function reveal() {{
    ticking = false;
    var limit = innerHeight * 0.92;
    pending = pending.filter(function (el) {{ if (el.getBoundingClientRect().top < limit) {{ el.classList.add('in'); return false; }} return true; }});
  }}
  addEventListener('scroll', function () {{ onScroll(); if (!ticking && pending.length) {{ ticking = true; requestAnimationFrame(reveal); }} }}, {{passive: true}});
  addEventListener('resize', reveal); onScroll(); reveal();
  // on phones the table of contents starts folded so the article begins right away
  if (innerWidth < 1000) document.querySelectorAll('.toc details').forEach(function (t) {{ t.open = false; }});
  var calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!calm) {{
    // headline words rise one by one; the text stays in the DOM for readers and crawlers
    document.querySelectorAll('.a-hero h1, .b-hero h1').forEach(function (h) {{
      var words = h.textContent.trim().split(/\s+/);
      h.setAttribute('aria-label', h.textContent.trim());
      h.innerHTML = words.map(function (w, i) {{ return '<span class="w" aria-hidden="true"><span style="--i:' + i + '">' + w.replace(/</g, '&lt;') + '</span></span>'; }}).join(' ');
      h.classList.add('words');
    }});
    // buttons lean toward the pointer a little
    if (matchMedia('(pointer: fine)').matches) document.querySelectorAll('.app-cta .btn, .featured .btn').forEach(function (b) {{
      b.classList.add('magnetic');
      b.addEventListener('mousemove', function (e) {{ var r = b.getBoundingClientRect(); b.style.transform = 'translate(' + (e.clientX - r.left - r.width / 2) * .18 + 'px,' + (e.clientY - r.top - r.height / 2) * .3 + 'px)'; }});
      b.addEventListener('mouseleave', function () {{ b.style.transform = ''; }});
    }});
  }}
  var q = document.getElementById('ara');
  if (q) q.addEventListener('input', function () {{
    var t = q.value.toLocaleLowerCase('tr');
    document.querySelectorAll('[data-search]').forEach(function (c) {{ c.hidden = t && c.dataset.search.indexOf(t) < 0; }});
  }});
}})();
</script>
</body>
</html>
'''


def app_card(course, big=False):
    phone = '<div class="cta-phone"><img src="/assets/ekran/01_bugun.jpg" alt="Uslu Bugün ekranı" loading="lazy" width="300" height="652"></div>'
    title = 'Köpeğine özel planla, her gün birkaç dakika' if big else 'Bu adımları günlük görevlere böl'
    text = (f'Uslu, köpeğinin yaşına ve zorlandığı konulara göre bir plan hazırlar. “{esc(course)}” kursu bu makaledeki adımları kısa, ödüllü derslere çevirir; antrenman ekranı seni adım adım yönlendirir.'
            if course else 'Uslu, köpeğinin yaşına ve zorlandığı konulara göre bir plan hazırlar ve her gün kısa, ödüllü dersler sunar.')
    return f'''
<aside class="app-cta reveal{' big' if big else ''}">
  <div class="cta-text">
    <span class="chip">Uslu uygulaması</span>
    <h3>{title}</h3>
    <p>{text}</p>
    <a class="btn" href="{APP_URL}"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.4 12.6c0-2.4 2-3.6 2.1-3.7-1.2-1.7-3-1.9-3.6-2-1.5-.2-3 .9-3.8.9-.8 0-2-.9-3.3-.9-1.7 0-3.3 1-4.2 2.5-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8 1.6 0 2 .8 3.3.8 1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.8-1-2.8-4.2zM13.9 5.1c.7-.8 1.2-2 1-3.1-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.9-1.4z"/></svg>{APP_CTA}</a>
    <span class="note">iPhone, iPad ve iPhone Duo için · Yalnızca ödüle dayalı yöntemler</span>
  </div>
  {phone}
  <img class="bob o1" src="/assets/nesneler/kemik.svg" alt="" loading="lazy">
  <img class="bob o2" src="/assets/nesneler/top.svg" alt="" loading="lazy">
</aside>'''


def card(p, i=0):
    name, color, icon = CATS[p['category']]
    search = esc(f"{p['title']} {p.get('keyword', '')} {' '.join(p['keywords'])} {name}".lower())
    return f'''
<a class="post-card reveal" href="/blog/{p['slug']}/" style="--c:{color};--d:{(i % 6) * 60}ms" data-search="{search}">
  <div class="pc-art"><img src="/assets/nesneler/{icon}.svg" alt="" loading="lazy" width="72" height="72"></div>
  <span class="chip">{name}</span>
  <h3>{esc(p['title'])}</h3>
  <p>{esc(p['description'])}</p>
  <span class="meta">{p['minutes']} dk okuma</span>
</a>'''


def jsonld(obj):
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


ORG = {'@type': 'Organization', '@id': f'{SITE}/#org', 'name': 'Protrom Yazılım ve Ticaret A.Ş.', 'url': SITE,
       'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/ikon.svg'}}


# ------------------------------------------------------------------ pages

def article_page(p, posts):
    name, color, icon = CATS[p['category']]
    url = f'{SITE}/blog/{p["slug"]}/'
    body, toc = render_body(p['body_md'])
    # the app card goes in before the third section, the second one closes the article
    parts = re.split(r'(?=<h2 )', body)
    if len(parts) > 3:
        parts.insert(3, app_card(p.get('course')))
        body = ''.join(parts)
    else:
        body += app_card(p.get('course'))
    toc_html = ''.join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in toc)
    faq_html = ''.join(f'<details class="qa reveal"><summary>{esc(f["q"])}</summary><p>{esc(f["a"])}</p></details>' for f in p['faq'])
    src_html = ''.join(f'<li>{source_link(s)}</li>' for s in p['sources'])
    related = [q for q in posts if q['category'] == p['category'] and q['slug'] != p['slug']]
    related += [q for q in posts if q['category'] != p['category'] and q['slug'] != p['slug']]
    rel_html = ''.join(card(q, i) for i, q in enumerate(related[:3]))
    og = f'{SITE}/blog/og/{p["slug"]}.png'
    title = p.get('seo_title') or p['title']
    ld = [
        {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': p['title'], 'description': p['description'],
         'image': og, 'datePublished': p['date'].isoformat(), 'dateModified': p.get('updated', p['date']).isoformat() if isinstance(p.get('updated', p['date']), dt.date) else str(p['updated']),
         'inLanguage': 'tr-TR', 'mainEntityOfPage': url, 'url': url, 'wordCount': p['words'],
         'keywords': ', '.join([p.get('keyword', '')] + p['keywords']), 'articleSection': name,
         'author': {'@type': 'Organization', 'name': 'Uslu ekibi', 'url': SITE}, 'publisher': ORG,
         'about': {'@type': 'Thing', 'name': p.get('keyword', p['title'])},
         'citation': [s for s in p['sources']]},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Uslu', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Blog', 'item': SITE + '/blog/'},
            {'@type': 'ListItem', 'position': 3, 'name': name, 'item': f'{SITE}/blog/kategori/{p["category"]}/'},
            {'@type': 'ListItem', 'position': 4, 'name': p['title'], 'item': url}]},
    ]
    if p['faq']:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in p['faq']]})
    extra = (f'<meta property="article:published_time" content="{p["date"].isoformat()}">'
             f'<meta property="article:section" content="{esc(name)}">' + ''.join(jsonld(x) for x in ld))
    return head(f'{title} | Uslu Blog', p['description'], url, og, extra, 'article') + f'''
<main class="article" style="--c:{color}">
  <div class="a-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Konum"><a href="/">Uslu</a><span>›</span><a href="/blog/">Blog</a><span>›</span><a href="/blog/kategori/{p['category']}/">{name}</a></nav>
      <span class="chip">{name}</span>
      <h1>{esc(p['title'])}</h1>
      <p class="byline">Uslu ekibi · {tr_date(p['date'])} · {p['minutes']} dk okuma · Hakemli araştırmalara dayanır</p>
      {dog(POSES[p['category']], 'hero-dog')}
      <img class="drift d1" src="/assets/nesneler/{icon}.svg" alt="">
      <img class="drift d2" src="/assets/nesneler/kemik.svg" alt="">
    </div>
  </div>
  <div class="wrap a-grid">
    <aside class="toc">
      <details open><summary>İçindekiler</summary><ol>{toc_html}<li><a href="#sss">Sık sorulan sorular</a></li><li><a href="#kaynaklar">Kaynaklar</a></li></ol></details>
    </aside>
    <article class="prose">
      <div class="tldr"><b>Kısaca</b><p>{esc(p.get('summary', p['description']))}</p></div>
      {body}
      <section class="faqs" id="sss"><h2>Sık sorulan sorular</h2>{faq_html}</section>
      <section class="sources" id="kaynaklar"><h2>Kaynaklar</h2><ol>{src_html}</ol>
        <p class="disclaimer">Bu yazı genel bilgilendirme amaçlıdır ve veteriner hekim muayenesinin yerini tutmaz. Köpeğinizde ağrı, ani davranış değişikliği ya da saldırganlık görürseniz veteriner hekiminize veya bir davranış uzmanına danışın.</p>
      </section>
      <div class="author reveal"><img src="/assets/ikon.svg" alt="" width="56" height="56"><div><b>Uslu ekibi</b><p>Uslu'nun içerikleri, köpek eğitimi ve davranışı üzerine yayımlanmış hakemli araştırmalara dayanır ve yalnızca ödüle dayalı yöntemleri anlatır. Protrom Yazılım ve Ticaret A.Ş. tarafından hazırlanır.</p></div></div>
    </article>
  </div>
  <section class="more">
    <div class="wrap">
      {app_card(p.get('course'), big=True)}
      <h2 class="reveal">Bunları da okuyabilirsin</h2>
      <div class="post-grid">{rel_html}</div>
    </div>
  </section>
</main>''' + foot(posts)


def index_page(posts, cat=None):
    shown = [p for p in posts if cat is None or p['category'] == cat]
    if cat:
        name, color, icon = CATS[cat]
        url = f'{SITE}/blog/kategori/{cat}/'
        title = f'{name}: köpek eğitimi yazıları | Uslu Blog'
        desc = f'{name} üzerine araştırmalara dayanan, adım adım ve yalnızca ödüle dayalı köpek eğitimi yazıları.'
        h1 = name
        lead = desc
    else:
        url = f'{SITE}/blog/'
        title = 'Köpek eğitimi blogu: ödülle eğitim rehberleri | Uslu'
        desc = 'Tuvalet eğitimi, havlama, ısırma, çağırınca gelme ve daha fazlası. Bilimsel araştırmalara dayanan, adım adım ve yalnızca ödüle dayalı köpek eğitimi rehberleri.'
        h1 = 'Köpek eğitimi blogu'
        lead = 'Köpeğinle yaşadığın sorunlara bilimsel araştırmalara dayanan, adım adım ve yalnızca ödüle dayalı çözümler.'
    chips = ''.join(f'<a class="chip{" on" if k == cat else ""}" href="/blog/kategori/{k}/" style="--c:{v[1]}">{v[0]}</a>' for k, v in CATS.items())
    chips = f'<a class="chip{" on" if cat is None else ""}" href="/blog/">Tümü</a>' + chips
    featured = '' if cat else f'''
  <a class="featured reveal" href="/blog/{shown[0]['slug']}/" style="--c:{CATS[shown[0]['category']][1]}">
    <div><span class="chip">{CATS[shown[0]['category']][0]}</span><h2>{esc(shown[0]['title'])}</h2><p>{esc(shown[0]['description'])}</p><span class="btn">Okumaya başla</span></div>
    {dog('fistik_zipliyor_sol', 'f-dog')}
  </a>'''
    grid = ''.join(card(p, i) for i, p in enumerate(shown[0 if cat else 1:]))
    ld = [{'@context': 'https://schema.org', '@type': 'Blog' if not cat else 'CollectionPage', 'name': h1, 'url': url, 'description': desc,
           'inLanguage': 'tr-TR', 'publisher': ORG,
           'blogPost' if not cat else 'hasPart': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': f'{SITE}/blog/{p["slug"]}/',
                                                    'datePublished': p['date'].isoformat()} for p in shown]}]
    return head(title, desc, url, f'{SITE}/blog/og/blog.png', ''.join(jsonld(x) for x in ld)) + f'''
<main class="blog-index">
  <div class="b-hero">
    <div class="wrap">
      <span class="eyebrow">Uslu Blog</span>
      <h1>{h1}</h1>
      <p class="lead">{lead}</p>
      <label class="search"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M11 4a7 7 0 1 1 0 14 7 7 0 0 1 0-14zm5 12 5 5"/></svg><input id="ara" type="search" placeholder="Ne öğrenmek istiyorsun? Örneğin havlama" aria-label="Yazılarda ara"></label>
      <div class="chips">{chips}</div>
      {dog(POSES[cat] if cat else 'fistik_onden_oturuyor_gulen', 'hero-dog')}
      <img class="drift d1" src="/assets/nesneler/kemik.svg" alt=""><img class="drift d2" src="/assets/nesneler/top.svg" alt=""><img class="drift d3" src="/assets/nesneler/kalp.svg" alt="">
    </div>
  </div>
  <div class="wrap">
    {featured}
    <div class="post-grid">{grid}</div>
    {app_card(None, big=True)}
  </div>
</main>''' + foot(posts)


# ------------------------------------------------------------------ feeds and crawler files

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)


def sitemap(posts):
    today = dt.date.today().isoformat()
    urls = [(SITE + '/', today, '1.0'), (SITE + '/blog/', today, '0.9')]
    urls += [(f'{SITE}/blog/kategori/{k}/', today, '0.6') for k in CATS]
    urls += [(f'{SITE}/blog/{p["slug"]}/', p['date'].isoformat(), '0.8') for p in posts]
    urls += [(SITE + '/destek.html', today, '0.4'), (SITE + '/gizlilik.html', today, '0.3')]
    items = ''.join(f'<url><loc>{u}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>' for u, d, pr in urls)
    write(os.path.join(WEB, 'sitemap.xml'), f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>\n')


def robots():
    write(os.path.join(WEB, 'robots.txt'), f'''# Uslu: everyone, including AI assistants, may read and cite the blog.
User-agent: *
Allow: /
Disallow: /panel/

User-agent: GPTBot
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: ClaudeBot
User-agent: Claude-SearchBot
User-agent: PerplexityBot
User-agent: Google-Extended
User-agent: Applebot-Extended
Allow: /
Disallow: /panel/

Sitemap: {SITE}/sitemap.xml
''')


def rss(posts):
    items = ''.join(f'''<item><title>{esc(p['title'])}</title><link>{SITE}/blog/{p['slug']}/</link><guid>{SITE}/blog/{p['slug']}/</guid>
<pubDate>{dt.datetime.combine(p['date'], dt.time(9)).strftime('%a, %d %b %Y %H:%M:%S +0300')}</pubDate><description>{esc(p['description'])}</description></item>''' for p in posts)
    write(os.path.join(OUT, 'feed.xml'), f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Uslu Blog</title><link>{SITE}/blog/</link><language>tr</language>
<description>Bilimsel araştırmalara dayanan, yalnızca ödüle dayalı köpek eğitimi rehberleri.</description>{items}</channel></rss>
''')


def llms(posts):
    lines = ['# Uslu', '',
             '> Uslu, Türkçe bir köpek eğitimi uygulamasıdır (iPhone, iPad, iPhone Duo). Köpeğe özel plan hazırlar, yalnızca ödüle dayalı kısa dersler, sağlık ve bakım takibi ve cihaz içinde çalışan bir asistan sunar. Protrom Yazılım ve Ticaret A.Ş. geliştirir.',
             '', 'Blog yazıları hakemli araştırmalara dayanır, her yazının sonunda kaynakları ve sık sorulan soruları vardır. Alıntılarken yazının adresini belirtin.', '',
             '## Blog']
    for k, (name, _, _) in CATS.items():
        group = [p for p in posts if p['category'] == k]
        if group:
            lines += ['', f'### {name}'] + [f'- [{p["title"]}]({SITE}/blog/{p["slug"]}/): {p.get("summary", p["description"])}' for p in group]
    lines += ['', '## Uygulama', f'- [Ana sayfa]({SITE}/): özellikler ve ekranlar', f'- [Destek]({SITE}/destek.html)', f'- [Gizlilik politikası]({SITE}/gizlilik.html)',
              '', '## Tam metin', f'- [llms-full.txt]({SITE}/llms-full.txt): tüm blog yazılarının tam metni']
    write(os.path.join(WEB, 'llms.txt'), '\n'.join(lines) + '\n')
    full = ['# Uslu blog, tam metin', '']
    for p in posts:
        full += [f'# {p["title"]}', f'Adres: {SITE}/blog/{p["slug"]}/', f'Yayın: {p["date"].isoformat()}', '', f'Kısaca: {p.get("summary", p["description"])}', '',
                 p['body_md'], '', '## Sık sorulan sorular'] + [f'**{f["q"]}** {f["a"]}' for f in p['faq']] + ['', '## Kaynaklar'] + [f'- {s}' for s in p['sources']] + ['', '---', '']
    write(os.path.join(WEB, 'llms-full.txt'), '\n'.join(full))


# ------------------------------------------------------------------ OG images

def og_images(posts):
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    os.makedirs(os.path.join(OUT, 'og'), exist_ok=True)
    fonts = os.path.join(WEB, 'assets', 'fonts')
    items = [(p['slug'], p['title'], CATS[p['category']], POSES[p['category']]) for p in posts]
    items.append(('blog', 'Köpek eğitimi blogu', ('Uslu Blog', '#FFE3A2', 'kemik'), 'fistik_onden_oturuyor_gulen'))
    for slug, title, (cname, color, icon), pose in items:
        page = f'''<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:I;src:url(file://{fonts}/InstrumentSerif-Regular.ttf)}}
@font-face{{font-family:G;src:url(file://{fonts}/Geist-SemiBold.ttf)}}
@font-face{{font-family:P;src:url(file://{fonts}/Pacifico-Regular.ttf)}}
html,body{{margin:0;width:1200px;height:630px;overflow:hidden;background:{color};font-family:G;color:#151515}}
.t{{position:absolute;left:72px;top:150px;width:700px;font:400 68px/1.02 I}}
.c{{position:absolute;left:72px;top:84px;background:#fff;border-radius:99px;padding:10px 20px;font-size:22px}}
.l{{position:absolute;left:72px;bottom:60px;font:400 46px P}} .u{{position:absolute;left:190px;bottom:72px;font-size:22px;opacity:.7}}
.d{{position:absolute;right:40px;bottom:36px;width:400px;height:470px;object-fit:contain;object-position:bottom}} .o{{position:absolute;right:360px;top:70px;width:90px;transform:rotate(-12deg)}}
</style><div class="c">{esc(cname)}</div><div class="t">{esc(title)}</div><div class="l">Uslu</div><div class="u">usluapp.co/blog</div>
<img class="o" src="file://{WEB}/assets/nesneler/{icon}.svg"><img class="d" src="file://{WEB}/assets/fistik/{pose}.svg">'''
        tmp = os.path.join(OUT, 'og', '_tmp.html')
        open(tmp, 'w', encoding='utf-8').write(page)
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                        '--force-device-scale-factor=1', '--virtual-time-budget=2000', '--window-size=1200,630',
                        f'--screenshot={os.path.join(OUT, "og", slug + ".png")}', f'file://{tmp}'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(tmp)


def home_latest(posts):
    """Three guides on the homepage, between the blog:son markers in web/index.html."""
    pick = ['kopek-egitimi-nasil-yapilir', 'yavru-kopek-tuvalet-egitimi', 'kopek-havlamasi-nasil-durdurulur']
    chosen = [p for s in pick for p in posts if p['slug'] == s]
    chosen += [p for p in posts if p not in chosen][:3 - len(chosen)]
    cards = ''.join(f'<a href="/blog/{p["slug"]}/" style="--c:{CATS[p["category"]][1]}">'
                    f'<img src="assets/nesneler/{CATS[p["category"]][2]}.svg" alt="" loading="lazy">'
                    f'<b>{esc(p["title"])}</b><span>{CATS[p["category"]][0]} · {p["minutes"]} dk okuma</span></a>' for p in chosen)
    path = os.path.join(WEB, 'index.html')
    page = open(path, encoding='utf-8').read()
    page = re.sub(r'<!-- blog:son -->.*?<!-- /blog:son -->', lambda m: f'<!-- blog:son --><div class="blog-son">{cards}</div><!-- /blog:son -->', page, flags=re.S)
    write(path, page)


def main():
    posts = load_posts()
    if not posts:
        sys.exit('no posts')
    css = os.path.join(OUT, 'blog.css')
    keep_css = open(css, encoding='utf-8').read() if os.path.exists(css) else None
    for name in os.listdir(OUT) if os.path.exists(OUT) else []:
        path = os.path.join(OUT, name)
        if os.path.isdir(path) and name not in ('og',):
            shutil.rmtree(path)
    if keep_css is not None:
        write(css, keep_css)
    for p in posts:
        write(os.path.join(OUT, p['slug'], 'index.html'), article_page(p, posts))
    write(os.path.join(OUT, 'index.html'), index_page(posts))
    for k in CATS:
        write(os.path.join(OUT, 'kategori', k, 'index.html'), index_page(posts, k))
    sitemap(posts)
    robots()
    rss(posts)
    llms(posts)
    home_latest(posts)
    if '--no-og' not in sys.argv:
        og_images(posts)
    print(f'{len(posts)} yazı, {sum(p["words"] for p in posts)} kelime')


if __name__ == '__main__':
    main()
