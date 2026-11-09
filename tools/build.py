#!/usr/bin/env python3
"""Генератор статического сайта «Альфа Бакалея».

Собирает HTML-страницы из общего шаблона и assets/data/products.json.
Запуск из корня репозитория:  python3 tools/build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = json.loads((ROOT / "assets/data/products.json").read_text(encoding="utf-8"))

PHONE = "+375 44 757 99 34"
PHONE_HREF = "tel:+375447579934"
EMAIL = "info@a-b.pro"
OFFICE = "Минск, Логойский тракт 37, БЦ «Норд Сити», 8-й этаж"

CATEGORIES = [
    ("sunflower-oil", "Подсолнечное масло", "Рафинированное и нерафинированное, от 0,5 до 5 л"),
    ("mayonnaise", "Майонез", "Провансаль, оливковый, на перепелиных яйцах"),
    ("ketchup", "Кетчуп", "Томатный, шашлычный, острый, лечо"),
    ("mayonnaise-sauces", "Майонезные соусы", "Чесночный, сырный, грибной, цезарь"),
    ("econom", "Масла эконом-сегмента", "Доступные масла для розницы и HoReCa"),
    ("shrot", "Шрот подсолнечника", "Ценный кормовой продукт для животноводства"),
]
CAT_NAME = {k: n for k, n, _ in CATEGORIES}

NAV = [
    ("index.html", "Главная"),
    ("catalog.html", "Каталог"),
    ("about.html", "О компании"),
    ("distribution.html", "Производители"),
    ("contacts.html", "Контакты"),
]

e = html.escape


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} {few}"
    return f"{n} {many}"


def count_products(n):
    return plural(n, "продукт", "продукта", "продуктов")


def volume(name):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(мл|л)\b", name)
    if not m:
        return ""
    return f"{m.group(1).replace('.', ',')} {m.group(2)}"


ABBR = [(r"\bнераф\.?(?=\s|$)", "нерафинированное"), (r"\bраф\.?(?=\s|$)", "рафинированное"),
        (r"\bподсолн\.", "подсолнечное")]

SECTIONS = ["Описание", "Состав", "Пищевая ценность на 100 г", "Пищевая ценность", "В одной порции содержится",
            "Условия и сроки хранения", "Условия и срок хранения"]


def parse_desc(text):
    """Разбирает описание с сайта на штрих-код, кратность и смысловые разделы."""
    out = {"barcode": "", "pack": "", "sections": []}
    t = text
    m = re.search(r"Штрих-код:\s*(\d+)", t)
    if m:
        out["barcode"] = m.group(1)
        t = t.replace(m.group(0), "")
    m = re.search(r"Кол-во в одном месте:\s*(\d+)", t)
    if m:
        out["pack"] = m.group(1)
        t = t.replace(m.group(0), "")
    t = t.strip()
    pat = "(" + "|".join(re.escape(x) for x in SECTIONS) + r"):?"
    parts = re.split(pat, t)
    lead = parts[0].strip(" .:")
    if lead:
        out["sections"].append(["Описание", lead])
    for i in range(1, len(parts), 2):
        title = parts[i].replace("Условия и срок хранения", "Условия и сроки хранения")
        body = parts[i + 1].strip(" :.—-")
        if not body:
            continue
        body = body[0].upper() + body[1:]
        if title.startswith("Пищевая ценность") or title.startswith("В одной порции"):
            title = "Пищевая ценность" if "100" not in title else "Пищевая ценность на 100 г"
        if out["sections"] and out["sections"][-1][0] == title:
            out["sections"][-1][1] += ". " + body
        else:
            out["sections"].append([title, body])
    return out


def short_name(p):
    """Имя без объёма — для заголовка карточки."""
    n = p["name"]
    for a, b in ABBR:
        n = re.sub(a, b, n)
    n = re.sub(r",?\s*\d+(?:[.,]\d+)?\s*(мл|л)\.?\s*$", "", n).strip(" ,.-—")
    n = n.replace("» -", "» —").replace("»-", "» —").replace("«", "«").strip()
    return n


def cats_of(p):
    return [c for c, _, _ in CATEGORIES if c in p["cats"]]


def primary_cat(p):
    cs = cats_of(p)
    # эконом-масла относим к своему разделу, чтобы не дублировать
    if "econom" in cs:
        return "econom"
    return cs[0] if cs else "sunflower-oil"


ICONS = {
    "box": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8 12 3 3 8v8l9 5 9-5V8Z"/><path d="m3 8 9 5 9-5M12 13v8"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M1 6h13v10H1zM14 10h4l4 4v2h-8"/><circle cx="5.5" cy="18" r="2"/><circle cx="17.5" cy="18" r="2"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/></svg>',
    "people": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="7" r="4"/><path d="M2 21v-1a7 7 0 0 1 14 0v1M16 3.1a4 4 0 0 1 0 7.8M22 21v-1a7 7 0 0 0-4-6.3"/></svg>',
    "card": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/></svg>',
    "handshake": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m11 17 2 2a1 1 0 1 0 3-3"/><path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.9-3.9a3 3 0 0 0-4.2 0l-.9.9a1 1 0 1 1-3-3l2.8-2.8a5.8 5.8 0 0 1 7.1-.9l.5.3a2 2 0 0 0 1.4.3L21 4"/><path d="m21 3 1 11h-2M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3M3 4h8"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
}


def feature(icon, title, text, cls=""):
    return f'''<div class="feature reveal {cls}"><div class="feature-icon">{ICONS[icon]}</div><h3>{title}</h3><p>{text}</p></div>'''


def product_card(p, lazy=True):
    vol = volume(p["name"])
    brand = p["brand"] or CAT_NAME.get(primary_cat(p), "")
    attrs = (
        f'data-id="{p["id"]}" data-cats="{" ".join(cats_of(p))}" '
        f'data-brand="{e(p["brand"])}" data-search="{e((p["name"] + " " + p["brand"]).lower())}"'
    )
    return f'''<a class="product" href="catalog.html#p-{p["id"]}" {attrs}>
  <div class="product-media"><img src="{p["img"]}" alt="{e(p["name"])}" width="800" height="800" {'loading="lazy" ' if lazy else ''}decoding="async"></div>
  <div class="product-body">
    <span class="product-badge">{e(brand)}</span>
    <span class="product-name">{e(short_name(p))}</span>
    {f'<span class="product-vol">{vol}</span>' if vol else ''}
    <span class="product-foot"><span class="link-arrow">Подробнее</span></span>
  </div>
</a>'''


def header(active):
    links = "".join(
        f'<li><a href="{href}"{" aria-current=\"page\"" if href == active else ""}>{name}</a></li>'
        for href, name in NAV
    )
    return f'''<header class="nav" id="nav">
  <div class="wrap-wide nav-inner">
    <a class="nav-logo" href="index.html" aria-label="Альфа Бакалея — на главную"><img src="assets/img/brand/logo.png" alt="Альфа Бакалея" width="800" height="313"></a>
    <nav aria-label="Основное меню"><ul class="nav-links" id="nav-links">{links}</ul></nav>
    <div class="nav-actions">
      <a class="nav-phone" href="{PHONE_HREF}">{PHONE}</a>
      <a class="btn btn-primary btn-sm" href="contacts.html#request">Стать партнёром</a>
      <button class="nav-toggle" id="nav-toggle" aria-label="Меню" aria-expanded="false" aria-controls="nav-links"><span></span><span></span></button>
    </div>
  </div>
</header>'''


def footer():
    cats = "".join(f'<li><a href="catalog.html#{k}">{n}</a></li>' for k, n, _ in CATEGORIES)
    return f'''<footer class="footer">
  <div class="wrap-wide">
    <p class="footer-note">ООО «Альфа Бакалея» — оптовая продажа продуктов питания в Республике Беларусь. Безналичная оплата в BYN, RUB, USD, EUR. Собственные склады в Минской области, Могилёве и Гомеле.</p>
    <div class="footer-cols">
      <div><h4>Каталог</h4><ul>{cats}</ul></div>
      <div><h4>Компания</h4><ul><li><a href="about.html">О компании</a></li><li><a href="distribution.html">Производители</a></li><li><a href="about.html#partners">Партнёры</a></li><li><a href="contacts.html#warehouses">Склады</a></li></ul></div>
      <div><h4>Связаться</h4><ul><li><a href="{PHONE_HREF}">{PHONE}</a></li><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="contacts.html">{e(OFFICE)}</a></li></ul></div>
      <div><h4>Информация</h4><ul><li><a href="privacy.html">Политика cookie</a></li><li><a href="privacy.html#personal-data">Обработка персональных данных</a></li><li><a href="contacts.html#requisites">Реквизиты</a></li></ul></div>
    </div>
    <div class="footer-bottom">
      <span>© {2026} ООО «Альфа Бакалея». Все права защищены.</span>
      <ul><li><a href="privacy.html">Конфиденциальность</a></li><li><a href="contacts.html#requisites">Реквизиты</a></li><li><a href="https://a-b.pro/">a-b.pro</a></li></ul>
    </div>
  </div>
</footer>
<div class="cookie" id="cookie" role="dialog" aria-live="polite" aria-label="Уведомление о cookie">
  <p>Мы используем cookie, чтобы сайт работал лучше. <a href="privacy.html">Подробнее</a></p>
  <button class="btn btn-secondary btn-sm" data-cookie="decline">Отклонить</button>
  <button class="btn btn-primary btn-sm" data-cookie="accept">Принять</button>
</div>'''


def page(filename, title, description, body, active=None, extra_head="", scripts=""):
    full_title = f"{title} — Альфа Бакалея" if title else "Альфа Бакалея — оптовая продажа продуктов питания"
    doc = f'''<!doctype html>
<html lang="ru" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta name="theme-color" content="#f5f5f7">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="assets/img/categories/about-oil.jpg">
<meta property="og:locale" content="ru_RU">
<link rel="icon" href="assets/img/brand/favicon-32.png" sizes="32x32">
<link rel="icon" href="assets/img/brand/icon-192.png" sizes="192x192">
<link rel="apple-touch-icon" href="assets/img/brand/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
{extra_head}<script>document.documentElement.classList.remove('no-js')</script>
</head>
<body>
<a class="visually-hidden" href="#main">Перейти к содержимому</a>
{header(active or filename)}
<main id="main">
{body}
</main>
{footer()}
<script src="assets/js/main.js" defer></script>
{scripts}
</body>
</html>
'''
    (ROOT / filename).write_text(doc, encoding="utf-8")
    print("built", filename)


def by_id(i):
    return next(p for p in PRODUCTS if p["id"] == i)


def cat_counts():
    return {k: sum(1 for p in PRODUCTS if k in p["cats"]) for k, _, _ in CATEGORIES}


# ---------------------------------------------------------------- index.html
def build_index():
    counts = cat_counts()
    hero_imgs = [(15751, "hv-s"), (15812, "hv-m"), (15794, "hv-c"), (15847, "hv-m"), (15679, "hv-s")]
    hero = "".join(
        f'<img class="{cls}" src="assets/img/hero/{i}.jpg" alt="" fetchpriority="{"high" if cls == "hv-c" else "auto"}">'
        for i, cls in hero_imgs
    )
    cat_cards = "".join(
        f'''<a class="cat-card" href="catalog.html#{k}">
  <div class="cc-text"><div class="cc-count">{count_products(counts[k])}</div><div class="cc-title">{n}</div><p class="muted" style="font-size:15px;margin-top:6px">{d}</p></div>
  <div class="cc-img"><img src="assets/img/categories/{k}.jpg" alt="" loading="lazy" width="280" height="280"></div>
</a>'''
        for k, n, d in CATEGORIES
    )
    popular_ids = [15794, 15847, 15812, 15726, 15751, 15682, 15708, 15772]
    popular = "".join(product_card(by_id(i)) for i in popular_ids)
    partners = partner_marquee()

    body = f'''
<section class="hero hero-home">
  <div class="wrap">
    <p class="eyebrow reveal">Оптовая торговля продуктами питания</p>
    <h1 class="h-hero reveal reveal-d1">Альфа Бакалея.<br><span class="gradient-text">Вкус оптом.</span></h1>
    <p class="lead reveal reveal-d2">Подсолнечное масло, майонез, кетчуп и соусы от ведущих производителей — с собственного склада и с доставкой своим автопарком.</p>
    <div class="cta-row reveal reveal-d3">
      <a class="btn btn-primary" href="catalog.html">Перейти в каталог</a>
      <a class="link-arrow" href="contacts.html#request">Запросить прайс-лист</a>
    </div>
  </div>
  <div class="hero-visual" aria-hidden="true">{hero}</div>
</section>

<section class="tiles" aria-label="Основные направления">
  <a class="tile cover full" href="catalog.html#sunflower-oil">
    <img src="assets/img/categories/about-oil.jpg" alt="Подсолнечное масло «Золотая семечка»" loading="lazy">
    <div class="tile-copy">
      <h2 class="tile-title">Подсолнечное масло</h2>
      <p class="tile-sub">«Золотая семечка», «Слобода», «Злато», Altero и другие.</p>
      <div class="cta-row"><span class="btn btn-primary">Смотреть {counts["sunflower-oil"]} позиций</span></div>
    </div>
  </a>
  <a class="tile cover" href="catalog.html#ketchup">
    <img src="assets/img/categories/about-ketchup.jpg" alt="Кетчупы «Слобода»" loading="lazy">
    <div class="tile-copy">
      <h2 class="tile-title">Кетчуп</h2>
      <p class="tile-sub">Томатный. Шашлычный. Острый.</p>
      <div class="cta-row"><span class="link-arrow">Подробнее</span></div>
    </div>
  </a>
  <a class="tile cover" href="catalog.html#mayonnaise">
    <img src="assets/img/categories/about-mayo.jpg" alt="Майонезы и соусы «Слобода»" loading="lazy">
    <div class="tile-copy">
      <h2 class="tile-title">Майонез и соусы</h2>
      <p class="tile-sub">{counts["mayonnaise"] + counts["mayonnaise-sauces"]} вкусов на любой рецепт.</p>
      <div class="cta-row"><span class="link-arrow">Подробнее</span></div>
    </div>
  </a>
  <a class="tile white" href="catalog.html#shrot">
    <h2 class="tile-title">Шрот подсолнечника</h2>
    <p class="tile-sub">Повышает продуктивность скота и птицы.</p>
    <div class="cta-row"><span class="btn btn-primary">Узнать больше</span></div>
    <div class="tile-img"><img src="{by_id(15988)["img"]}" alt="Шрот подсолнечника" loading="lazy"></div>
  </a>
  <a class="tile dark" href="catalog.html#econom">
    <h2 class="tile-title">Эконом-сегмент</h2>
    <p class="tile-sub">Качество, доступное каждому.</p>
    <div class="cta-row"><span class="btn btn-primary">Смотреть</span></div>
    <div class="tile-img"><img src="{by_id(15824)["img"]}" alt="Масло «Южное солнце»" loading="lazy" style="mix-blend-mode:normal;border-radius:18px 18px 0 0"></div>
  </a>
</section>

<section class="section bg-alt">
  <div class="wrap-wide">
    <div class="section-head" style="text-align:left;margin-left:0">
      <h2 class="h2 reveal">Весь ассортимент. <span class="muted">Шесть категорий — {len(PRODUCTS)} позиций.</span></h2>
    </div>
  </div>
  <div class="scroller" id="cat-scroller">{cat_cards}</div>
  <div class="wrap-wide scroller-nav">
    <button class="scroller-btn" data-scroll="cat-scroller" data-dir="-1" aria-label="Назад">‹</button>
    <button class="scroller-btn" data-scroll="cat-scroller" data-dir="1" aria-label="Вперёд">›</button>
  </div>
</section>

<section class="section">
  <div class="wrap-wide">
    <div class="section-head">
      <h2 class="h2 reveal">Хиты продаж.</h2>
      <p class="lead reveal reveal-d1">То, что партнёры заказывают чаще всего.</p>
    </div>
    <div class="products">{popular}</div>
    <div class="cta-row"><a class="btn btn-secondary" href="catalog.html">Весь каталог</a></div>
  </div>
</section>

<section class="section bg-dark">
  <div class="wrap-wide">
    <div class="section-head">
      <p class="eyebrow reveal" style="color:#e2a93a">Почему «Альфа Бакалея»</p>
      <h2 class="h2 reveal reveal-d1">Надёжный партнёр.<br>На каждом этапе.</h2>
    </div>
    <div class="features">
      {feature("star", "Качество", "Только проверенная продукция от лидеров рынка — «Юг Руси» и «ЭФКО».")}
      {feature("people", "Профессионализм", "В команде только опытные специалисты: от менеджера до водителя.", "reveal-d1")}
      {feature("handshake", "Индивидуальный подход", "Гибкие условия сотрудничества и персональный менеджер для каждого клиента.", "reveal-d2")}
      {feature("box", "Собственные склады", "Четыре склада в Минской области, Могилёве и Гомеле — товар всегда в наличии.")}
      {feature("truck", "Свой автопарк", "16 машин доставляют заказы по всей Беларуси. Самовывоз — тоже можно.", "reveal-d1")}
      {feature("card", "Безналичная оплата", "Принимаем оплату в BYN, RUB, USD и EUR.", "reveal-d2")}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="stats">
      <div class="reveal"><div class="stat-num" data-count="2979">2979</div><div class="stat-label">партнёров</div></div>
      <div class="reveal reveal-d1"><div class="stat-num"><span data-count="192">192</span><small>млн</small></div><div class="stat-label">единиц товара отгружено</div></div>
      <div class="reveal reveal-d2"><div class="stat-num" data-count="16">16</div><div class="stat-label">машин в автопарке</div></div>
    </div>
    <div class="cta-row"><a class="link-arrow" href="about.html">Подробнее о компании</a></div>
  </div>
</section>

<section class="section-tight bg-alt" id="partners">
  <div class="wrap section-head" style="margin-bottom:40px">
    <h2 class="h2 reveal">Нас выбирают лучшие.</h2>
    <p class="lead reveal reveal-d1">Крупнейшие торговые сети Беларуси — наши партнёры.</p>
  </div>
  {partners}
</section>

<section class="section cta-band">
  <div class="wrap">
    <h2 class="h1 reveal">Давайте создадим<br>вкусный бизнес вместе.</h2>
    <p class="lead reveal reveal-d1">Оставьте заявку — менеджер подготовит прайс-лист и условия поставки.</p>
    <div class="cta-row reveal reveal-d2">
      <a class="btn btn-primary" href="contacts.html#request">Стать партнёром</a>
      <a class="link-arrow" href="{PHONE_HREF}">Позвонить {PHONE}</a>
    </div>
  </div>
</section>
'''
    page("index.html", "", "Альфа Бакалея — оптовая продажа подсолнечного масла, майонеза, кетчупа и соусов в Беларуси. Собственные склады и автопарк.", body)


PARTNERS = ["euroopt", "гиппо", "санта", "корона", "соседи", "белмаркет", "доброном", "Юнистор", "алми",
            "бертал", "грин", "два-гуся", "дионис", "мартин", "перекресток", "продтовары-1", "простор"]


def partner_marquee():
    items = "".join(
        f'<div class="partner"><img src="assets/img/partners/{n}.jpg" alt="{n.replace("-1", "").replace("-", " ").capitalize()}" loading="lazy"></div>'
        for n in PARTNERS
    )
    dup = items.replace('alt="', 'aria-hidden="true" alt="')
    return f'<div class="marquee"><div class="marquee-track">{items}{dup}</div></div>'


# -------------------------------------------------------------- catalog.html
def build_catalog():
    counts = cat_counts()
    chips = '<a class="cat-chip active" href="#all" data-cat="all"><span class="cc-thumb cc-all">Все</span>Все товары</a>' + "".join(
        f'<a class="cat-chip" href="#{k}" data-cat="{k}"><span class="cc-thumb"><img src="assets/img/categories/{k}.jpg" alt="" width="280" height="280"></span>{n}</a>'
        for k, n, _ in CATEGORIES
    )
    brands = sorted({p["brand"] for p in PRODUCTS if p["brand"]}, key=lambda b: (b.startswith("M") or b.startswith("A"), b))
    seg = '<button type="button" data-brand="" aria-pressed="true">Все бренды</button>' + "".join(
        f'<button type="button" data-brand="{e(b)}" aria-pressed="false">{e(b)}</button>' for b in brands
    )
    groups = []
    for k, n, d in CATEGORIES:
        items = [p for p in PRODUCTS if primary_cat(p) == k]
        items.sort(key=lambda p: (p["brand"] or "яя", p["name"]))
        cards = "".join(product_card(p) for p in items)
        groups.append(
            f'''<section class="catalog-group" id="{k}" data-group="{k}">
  <div class="catalog-group-head"><h2>{n}</h2><span>{d}</span></div>
  <div class="products">{cards}</div>
</section>'''
        )
    data = [
        {
            "id": p["id"], "name": p["name"], "title": short_name(p), "vol": volume(p["name"]),
            "brand": p["brand"], "cats": [CAT_NAME[c] for c in cats_of(p)], "img": p["img"], **parse_desc(p["desc"]),
        }
        for p in PRODUCTS
    ]
    body = f'''
<div class="subnav"><div class="wrap-wide"><span class="subnav-title">Каталог</span>
  <nav class="subnav-links" aria-label="Категории">{"".join(f'<a href="#{k}">{n}</a>' for k, n, _ in CATEGORIES)}</nav>
</div></div>

<section class="catalog-hero bg-alt">
  <div class="wrap">
    <h1 class="h1 reveal">Каталог продукции.</h1>
    <p class="lead reveal reveal-d1">{count_products(len(PRODUCTS)).capitalize()} от ведущих производителей. Цены и условия — по запросу.</p>
  </div>
  <div class="cat-strip reveal reveal-d2" role="tablist" aria-label="Категории">{chips}</div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap-wide">
    <div class="toolbar">
      <div class="segmented" role="group" aria-label="Бренд">{seg}</div>
      <label class="search"><span class="visually-hidden">Поиск по каталогу</span>{ICONS["search"]}<input type="search" id="q" placeholder="Поиск по каталогу" autocomplete="off"></label>
    </div>
    <p class="result-meta" id="result-meta" aria-live="polite">Показано {count_products(len(PRODUCTS))}</p>
    <div id="groups">{"".join(groups)}</div>
    <div class="empty" id="empty" hidden><p class="h3" style="color:var(--text)">Ничего не найдено.</p><p style="margin-top:8px">Попробуйте изменить запрос или <button class="link-arrow" style="color:var(--link)" id="reset">сбросить фильтры</button></p></div>
  </div>
</section>

<section class="section bg-alt cta-band">
  <div class="wrap">
    <h2 class="h2 reveal">Нужен прайс-лист?</h2>
    <p class="lead reveal reveal-d1">Пришлём актуальные цены и условия поставки для вашего бизнеса в течение рабочего дня.</p>
    <div class="cta-row reveal reveal-d2"><a class="btn btn-primary" href="contacts.html#request">Запросить прайс</a><a class="link-arrow" href="{PHONE_HREF}">{PHONE}</a></div>
  </div>
</section>

<dialog class="pd" id="pd" aria-labelledby="pd-title">
  <button class="pd-close" id="pd-close" aria-label="Закрыть">×</button>
  <div class="pd-grid">
    <div class="pd-media"><img id="pd-img" src="" alt=""></div>
    <div class="pd-body">
      <span class="product-badge" id="pd-brand"></span>
      <h2 id="pd-title"></h2>
      <div class="pd-sec" id="pd-desc"></div>
      <ul class="pd-specs" id="pd-specs"></ul>
      <div class="pd-actions">
        <a class="btn btn-primary" id="pd-request" href="contacts.html#request">Запросить цену</a>
        <a class="btn btn-secondary" href="{PHONE_HREF}">Позвонить</a>
      </div>
    </div>
  </div>
</dialog>
<script type="application/json" id="products-data">{json.dumps(data, ensure_ascii=False)}</script>
'''
    page("catalog.html", "Каталог", "Каталог «Альфа Бакалея»: подсолнечное масло, майонез, кетчуп, майонезные соусы, шрот подсолнечника оптом.", body,
         scripts='<script src="assets/js/catalog.js" defer></script>')


# ---------------------------------------------------------------- about.html
def build_about():
    body = f'''
<section class="hero" style="padding-bottom:clamp(56px,8vw,96px)">
  <div class="wrap">
    <p class="eyebrow reveal">О компании</p>
    <h1 class="h-hero reveal reveal-d1">Больше, чем<br>поставщик.</h1>
    <p class="lead reveal reveal-d2">«Альфа Бакалея» строит долгосрочные партнёрские отношения: надёжные поставки, продукты высочайшего качества и сервис, на который можно положиться.</p>
  </div>
</section>

<section class="section">
  <div class="wrap-wide split">
    <div class="split-media reveal"><img src="assets/img/categories/hero.jpg" alt="Диплом и награда компании «Альфа Бакалея»" loading="lazy"></div>
    <div class="split-copy reveal reveal-d1">
      <h2 class="h2">Опыт и репутация.</h2>
      <p>Компания «Альфа Бакалея» обладает опытом и репутацией надёжного поставщика в области оптовой торговли продуктами питания.</p>
      <p>Мы не просто предлагаем товары — мы становимся партнёрами наших клиентов: помогаем выбрать оптимальные решения, предлагаем гибкие условия сотрудничества и обеспечиваем оперативную доставку.</p>
    </div>
  </div>
</section>

<section class="section bg-dark">
  <div class="wrap">
    <div class="section-head"><h2 class="h2 reveal">О нас в цифрах.</h2></div>
    <div class="stats">
      <div class="reveal"><div class="stat-num" data-count="2979">2979</div><div class="stat-label">партнёров</div></div>
      <div class="reveal reveal-d1"><div class="stat-num"><span data-count="192">192</span><small>млн</small></div><div class="stat-label">единиц товара отгружено</div></div>
      <div class="reveal reveal-d2"><div class="stat-num" data-count="36">36</div><div class="stat-label">профессионалов в команде</div></div>
      <div class="reveal"><div class="stat-num" data-count="4">4</div><div class="stat-label">склада</div></div>
      <div class="reveal reveal-d1"><div class="stat-num" data-count="16">16</div><div class="stat-label">машин в автопарке</div></div>
      <div class="reveal reveal-d2"><div class="stat-num" data-count="{len(PRODUCTS)}">{len(PRODUCTS)}</div><div class="stat-label">позиций в каталоге</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap prose">
    <p class="reveal">Наше направление — широкий ассортимент продукции: от <strong>высококачественных подсолнечных масел</strong>, изготовленных из отборных семян подсолнечника по передовым технологиям, до <strong>майонезов, соусов и кетчупов</strong>, каждый из которых производится только из качественных ингредиентов.</p>
    <p class="reveal">Мы также предлагаем <strong>шрот подсолнечника</strong> — ценный кормовой продукт, который способствует повышению продуктивности скота и птицы.</p>
    <p class="reveal">Наше обязательство поставлять продукты, отвечающие самым высоким стандартам качества и безопасности, делает нас идеальным выбором для вашего бизнеса.</p>
  </div>
</section>

<section class="tiles" aria-label="Продукция">
  <a class="tile cover" href="catalog.html#sunflower-oil"><img src="assets/img/categories/about-oil.jpg" alt="" loading="lazy"><div class="tile-copy"><h2 class="tile-title">Масло</h2><p class="tile-sub">Из отборных семян подсолнечника.</p></div></a>
  <a class="tile cover" href="catalog.html#mayonnaise"><img src="assets/img/categories/about-mayo.jpg" alt="" loading="lazy"><div class="tile-copy"><h2 class="tile-title">Майонез и соусы</h2><p class="tile-sub">Натуральные ингредиенты.</p></div></a>
</section>

<section class="section bg-alt">
  <div class="wrap-wide">
    <div class="section-head"><h2 class="h2 reveal">Что мы гарантируем.</h2></div>
    <div class="features">
      {feature("truck", "Собственный склад и автопарк", "Удобная логистика: доставка по всей Беларуси и самовывоз.")}
      {feature("shield", "Контроль качества", "Каждый партнёр получает высочайший уровень обслуживания.", "reveal-d1")}
      {feature("star", "Лучшие бренды", "Эксклюзивное качество продуктов от наших партнёров-производителей.", "reveal-d2")}
    </div>
  </div>
</section>

<section class="section-tight" id="partners">
  <div class="wrap section-head" style="margin-bottom:40px">
    <h2 class="h2 reveal">Наши партнёры.</h2>
    <p class="lead reveal reveal-d1">Нам доверяют ведущие розничные сети страны.</p>
  </div>
  {partner_marquee()}
</section>

<section class="section bg-dark cta-band">
  <div class="wrap">
    <h2 class="h1 reveal">Присоединяйтесь к<br><span class="gradient-text">«Альфа Бакалея».</span></h2>
    <p class="lead reveal reveal-d1">И давайте вместе создадим вкусный и успешный бизнес.</p>
    <div class="cta-row reveal reveal-d2"><a class="btn btn-primary" href="contacts.html#request">Стать партнёром</a><a class="link-arrow" href="catalog.html">Смотреть каталог</a></div>
  </div>
</section>
'''
    page("about.html", "О компании", "«Альфа Бакалея» — надёжный партнёр в оптовой продаже продуктов питания: 2979 партнёров, 4 склада, 16 машин.", body)


# ---------------------------------------------------------- distribution.html
def build_distribution():
    brand_tags = lambda tags: "".join(f'<span class="tag">{t}</span>' for t in tags)
    body = f'''
<section class="hero" style="padding-bottom:clamp(56px,8vw,96px)">
  <div class="wrap">
    <p class="eyebrow reveal">Производители</p>
    <h1 class="h-hero reveal reveal-d1">Лидеры рынка.<br>В одном каталоге.</h1>
    <p class="lead reveal reveal-d2">«Альфа Бакалея» — дистрибьютор продукции крупнейших производителей подсолнечного масла, майонезов и соусов.</p>
  </div>
</section>

<section class="section-tight bg-alt">
  <div class="wrap-wide brand-cards">
    <article class="brand-card reveal">
      <div class="bc-logo"><img src="assets/img/brand/yug-rusi.svg" alt="ГК «Юг Руси»" loading="lazy"></div>
      <h3>ГК «Юг Руси»</h3>
      <p>Ведущий производитель подсолнечного масла в России и признанный участник международного рынка масла и зерновых. Основана в 1992 году в Ростове-на-Дону.</p>
      <div class="bc-tags">{brand_tags(["Золотая семечка", "Злато", "100 рецептов", "Altero"])}</div>
      <a class="link-arrow" href="#yug-rusi">Подробнее</a>
    </article>
    <article class="brand-card reveal reveal-d1">
      <div class="bc-logo"><img src="assets/img/brand/efko.png" alt="ГК «ЭФКО»" loading="lazy"></div>
      <h3>ГК «ЭФКО»</h3>
      <p>Крупнейший производственный комплекс в Алексеевке — там, где почти 200 лет назад впервые в Российской империи получили масло из семечек подсолнечника.</p>
      <div class="bc-tags">{brand_tags(["Слобода", "Master Gurme", "Добавкин"])}</div>
      <a class="link-arrow" href="#efko">Подробнее</a>
    </article>
  </div>
</section>

<section class="section" id="yug-rusi">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow reveal">ГК «Юг Руси»</p><h2 class="h2 reveal reveal-d1">30 лет пути —<br>от торговой компании до лидера.</h2></div>
    <div class="prose">
      <p class="reveal">За более чем 30 лет работы ГК «Юг Руси» прошла путь от маленькой торговой компании до ведущего производителя подсолнечного масла в России и признанного участника международного рынка подсолнечного масла и зерновых.</p>
      <p class="reveal">В <strong>2000 году</strong> «Юг Руси» впервые в России вывел на рынок рафинированное дезодорированное подсолнечное масло мирового уровня качества — <strong>«Золотая семечка»</strong>. С тех пор компания лидирует на российском рынке бутилированного масла и расширяет портфель: «Злато», «АведовЪ», «Милора», «100 рецептов», «Раздолье» и другие.</p>
      <p class="reveal">Производственная и логистическая база включает сеть маслозаводов, элеваторов, собственный портовый терминал в Азово-Черноморском бассейне и автотранспортную компанию.</p>
    </div>
  </div>
</section>

<section class="section-tight">
  <div class="wrap">
    <div class="stats">
      <div class="reveal"><div class="stat-num">1992</div><div class="stat-label">год основания</div></div>
      <div class="reveal reveal-d1"><div class="stat-num" data-count="5000">5000</div><div class="stat-label">фермеров-поставщиков</div></div>
      <div class="reveal reveal-d2"><div class="stat-num" data-count="400">400</div><div class="stat-label">дистрибьюторских компаний</div></div>
    </div>
  </div>
</section>

<section class="tiles"><a class="tile cover full" href="catalog.html#sunflower-oil"><img src="assets/img/categories/about-oil.jpg" alt="" loading="lazy"><div class="tile-copy"><h2 class="tile-title">«Золотая семечка»</h2><p class="tile-sub">Масло мирового уровня с 2000 года.</p><div class="cta-row"><span class="btn btn-primary">В каталог</span></div></div></a></section>

<section class="section bg-dark" id="efko">
  <div class="wrap">
    <div class="section-head"><p class="eyebrow reveal" style="color:#e2a93a">ГК «ЭФКО»</p><h2 class="h2 reveal reveal-d1">Большая идея превращает бизнес<br>в удивительное приключение.</h2></div>
    <div class="prose">
      <p class="reveal">В Алексеевской слободе в конце 20-х годов XIX века впервые на территории Российской империи было получено масло из семечек подсолнечника и построен первый маслобойный завод. Спустя почти 200 лет <strong>Алексеевка остаётся крупнейшим центром переработки подсолнечника</strong> — здесь находится крупнейший производственный комплекс «ЭФКО».</p>
      <p class="reveal">Проанализировав глобальные вызовы в области экологии и устойчивого развития, «ЭФКО» переосмыслила подход к бизнесу и сделала ставку на современные, экологичные и технологичные решения.</p>
    </div>
  </div>
</section>
<section class="section-tight bg-dark" style="padding-top:0">
  <div class="wrap-wide">
    <ol class="timeline">
      <li class="reveal"><div class="tl-year">2020</div><p>Начало производства растительного мяса.</p></li>
      <li class="reveal reveal-d1"><div class="tl-year">2021</div><p>Продажа животноводческих активов.</p></li>
      <li class="reveal reveal-d2"><div class="tl-year">2022</div><p>Первые в России образцы масла, полученного в лабораторных условиях.</p></li>
      <li class="reveal reveal-d3"><div class="tl-year">2023</div><p>Сладкие белки — полезная альтернатива сахару.</p></li>
    </ol>
  </div>
</section>

<section class="section cta-band">
  <div class="wrap">
    <h2 class="h2 reveal">Продукция «Слобода», «Золотая семечка»<br>и других брендов — оптом.</h2>
    <div class="cta-row reveal reveal-d1"><a class="btn btn-primary" href="catalog.html">Открыть каталог</a><a class="link-arrow" href="contacts.html#request">Запросить прайс</a></div>
  </div>
</section>
'''
    page("distribution.html", "Производители", "«Альфа Бакалея» — дистрибьютор продукции ГК «Юг Руси» и ГК «ЭФКО»: «Золотая семечка», «Слобода», «Злато», Master Gurme.", body)


# -------------------------------------------------------------- contacts.html
def build_contacts():
    warehouses = [
        ("Могилёв", "ул. Залуцкого, д. 23"),
        ("Гомель", "ул. Владимирова, д. 6"),
        ("Смолевичи", "ул. Социалистическая, д. 32"),
        ("Смолевичский район", "д. Черница, д. 3, корп. 3"),
    ]
    wh = "".join(
        f'<li class="reveal{" reveal-d1" if i % 2 else ""}"><span class="wh-num">{i + 1}</span><div><div class="wh-city">{c}</div><div class="wh-addr">{a}</div></div></li>'
        for i, (c, a) in enumerate(warehouses)
    )
    reqs = [
        ("Полное наименование", "Общество с ограниченной ответственностью «Альфа Бакалея»"),
        ("Юридический адрес", "222201, Минская обл., г. Смолевичи, ул. Социалистическая, д. 32-6, каб. 74"),
        ("Адрес офиса", "г. Минск, Логойский тракт 37, БЦ «Норд Сити», 8-й этаж"),
        ("ОКПО", "505731846000"),
        ("Банк", "ЗАО «Альфа-Банк», ул. Сурганова, 43-47, 220013 Минск"),
        ("Код банка (BIC)", "ALFABY2X"),
        ("Расчётный счёт, BYN", "BY51 ALFA 3012 2B42 9500 1027 0000"),
        ("Текущий счёт, USD", "BY36 ALFA 3012 2B42 9500 2027 0000"),
        ("Текущий счёт, EUR", "BY21 ALFA 3012 2B42 9500 3027 0000"),
        ("Текущий счёт, RUB", "BY06 ALFA 3012 2B42 9500 4027 0000"),
        ("Директор", "Ильковец Александр Александрович, действует на основании Устава"),
    ]
    req_rows = "".join(f"<tr><th scope=\"row\">{a}</th><td>{b}</td></tr>" for a, b in reqs)
    cat_options = "".join(f"<option>{n}</option>" for _, n, _ in CATEGORIES)
    body = f'''
<section class="hero" style="padding-bottom:clamp(48px,6vw,72px)">
  <div class="wrap">
    <h1 class="h-hero reveal">Свяжитесь с нами.</h1>
    <p class="lead reveal reveal-d1">Ответим на вопросы, подготовим прайс-лист и условия поставки.</p>
  </div>
</section>

<section class="section-tight bg-alt" style="padding-top:0">
  <div class="wrap-wide">
    <div class="contact-grid">
      <div class="contact-card reveal"><span class="cc-label">Телефон</span><a class="cc-value" href="{PHONE_HREF}">{PHONE}</a><p>Мобильный, Viber, Telegram</p></div>
      <div class="contact-card reveal reveal-d1"><span class="cc-label">Email</span><a class="cc-value" href="mailto:{EMAIL}">{EMAIL}</a><p>Также: <a href="mailto:alfabakaleya@gmail.com">alfabakaleya@gmail.com</a></p></div>
      <div class="contact-card reveal reveal-d2"><span class="cc-label">Офис</span><span class="cc-value">Логойский тракт, 37</span><p>Минск, БЦ «Норд Сити», 8-й этаж</p></div>
    </div>
    <div class="map-wrap reveal">
      <iframe title="Офис «Альфа Бакалея» на карте" loading="lazy" src="https://yandex.by/map-widget/v1/?text=%D0%9C%D0%B8%D0%BD%D1%81%D0%BA%2C%20%D0%9B%D0%BE%D0%B3%D0%BE%D0%B9%D1%81%D0%BA%D0%B8%D0%B9%20%D1%82%D1%80%D0%B0%D0%BA%D1%82%2037&amp;z=16"></iframe>
    </div>
  </div>
</section>

<section class="section" id="request">
  <div class="wrap-wide split">
    <div class="split-copy reveal">
      <p class="eyebrow">Заявка</p>
      <h2 class="h2">Станьте партнёром.</h2>
      <p>Расскажите, какая продукция вас интересует, — менеджер свяжется с вами в течение рабочего дня и пришлёт актуальный прайс-лист.</p>
      <p>Или позвоните: <a href="{PHONE_HREF}">{PHONE}</a></p>
    </div>
    <form class="form reveal reveal-d1" id="request-form" novalidate>
      <div class="field"><label for="f-name">Имя</label><input id="f-name" name="name" autocomplete="name" required></div>
      <div class="field"><label for="f-company">Компания</label><input id="f-company" name="company" autocomplete="organization"></div>
      <div class="field-row">
        <div class="field"><label for="f-phone">Телефон</label><input id="f-phone" name="phone" type="tel" autocomplete="tel" required placeholder="+375"></div>
        <div class="field"><label for="f-email">Email</label><input id="f-email" name="email" type="email" autocomplete="email"></div>
      </div>
      <div class="field"><label for="f-cat">Интересует</label><select id="f-cat" name="category"><option>Весь ассортимент</option>{cat_options}</select></div>
      <div class="field"><label for="f-msg">Комментарий</label><textarea id="f-msg" name="message" rows="4"></textarea></div>
      <button class="btn btn-primary" type="submit">Отправить заявку</button>
      <p class="form-note">Нажимая кнопку, вы соглашаетесь с <a href="privacy.html#personal-data">обработкой персональных данных</a>. Заявка откроется в вашем почтовом приложении.</p>
    </form>
  </div>
</section>

<section class="section bg-alt" id="warehouses">
  <div class="wrap">
    <div class="section-head"><h2 class="h2 reveal">Наши склады.</h2><p class="lead reveal reveal-d1">Четыре склада — быстрая отгрузка по всей стране.</p></div>
    <ul class="warehouses">{wh}</ul>
  </div>
</section>

<section class="section" id="requisites">
  <div class="wrap">
    <div class="section-head"><h2 class="h2 reveal">Реквизиты.</h2></div>
    <table class="req-table reveal"><tbody>{req_rows}</tbody></table>
  </div>
</section>
'''
    page("contacts.html", "Контакты", "Контакты «Альфа Бакалея»: телефон +375 44 757 99 34, офис в Минске, склады в Могилёве, Гомеле и Смолевичах, реквизиты.", body)


def build_privacy():
    body = '''
<section class="hero" style="padding-bottom:clamp(40px,6vw,64px)"><div class="wrap"><h1 class="h1 reveal">Конфиденциальность.</h1><p class="lead reveal reveal-d1">Как мы используем cookie и обрабатываем персональные данные.</p></div></section>
<section class="section"><div class="wrap prose">
  <h2 class="h3" style="margin-bottom:16px">Политика обработки файлов cookie</h2>
  <p>Сайт a-b.pro использует файлы cookie для корректной работы, анализа посещаемости и улучшения пользовательского опыта. Вы можете отказаться от использования cookie в уведомлении на сайте или в настройках браузера.</p>
  <h2 class="h3" id="personal-data" style="margin:48px 0 16px">Обработка персональных данных</h2>
  <p>Отправляя заявку, вы предоставляете ООО «Альфа Бакалея» согласие на обработку указанных персональных данных (имя, наименование организации, телефон, email) исключительно в целях ответа на обращение и заключения договора поставки.</p>
  <p>Данные не передаются третьим лицам, за исключением случаев, предусмотренных законодательством Республики Беларусь. Для отзыва согласия напишите на <a href="mailto:info@a-b.pro">info@a-b.pro</a>.</p>
</div></section>
'''
    page("privacy.html", "Конфиденциальность", "Политика cookie и обработки персональных данных ООО «Альфа Бакалея».", body, active="")


if __name__ == "__main__":
    build_index()
    build_catalog()
    build_about()
    build_distribution()
    build_contacts()
    build_privacy()
