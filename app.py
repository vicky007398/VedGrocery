"""Public grocery catalog and private shopkeeper dashboard for Railway."""
import hmac
import html
import io
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from werkzeug.security import check_password_hash
from catalog_data import CATEGORIES, SUBCATEGORIES, TEMPLATES

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=bool(os.environ.get('RAILWAY_ENVIRONMENT_ID')),
    SEND_FILE_MAX_AGE_DEFAULT=timedelta(hours=12),
)
DATABASE_URL = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://', 1)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')
if os.environ.get('RAILWAY_ENVIRONMENT_ID') and not all((DATABASE_URL, os.environ.get('SECRET_KEY'), ADMIN_PASSWORD_HASH)):
    raise RuntimeError('Railway requires DATABASE_URL, SECRET_KEY and ADMIN_PASSWORD_HASH.')

# A short local cache avoids repeated cross-region database connections for
# public catalog reads. Admin writes invalidate the current process immediately;
# other replicas refresh within the TTL.
_cache_lock = threading.RLock()
_cache = {}
_pool_lock = threading.Lock()
_pg_pool = None


def cached(key, loader, ttl=30):
    with _cache_lock:
        item = _cache.get(key)
        if item and item[0] > time.monotonic():
            return item[1]
        value = loader()
        if len(_cache) > 128:
            _cache.clear()
        _cache[key] = (time.monotonic() + ttl, value)
        return value


def clear_cache():
    with _cache_lock:
        _cache.clear()

CATEGORY_IDS = {c[0] for c in CATEGORIES if c[0] != 'all'}
LEGACY_CATEGORY = {'vegetables':'fresh','grains':'staples','pulses':'staples',
                   'dairy':'fresh','cleaning':'household','bath':'care','puja':'household',
                   'oils':'oils','spices':'spices','beverages':'beverages'}
LEGACY_SUBCATEGORY = {'vegetables':'Staple Vegetables','grains':'Wheat & Millets',
                      'pulses':'Split Dals','dairy':'Milk','oils':'Cooking Oils',
                      'spices':'Powdered Spices','beverages':'Tea','cleaning':'Laundry',
                      'bath':'Soap','puja':'Daily Puja'}
SEARCH_ALIASES = {'Toor dal':'tuver tuvar arhar tur તુવેર',
                  'Tuver dal':'toor tur arhar તુવેર',
                  'Groundnut oil':'singtel singtel singtel સીંગતેલ',
                  'Sharbati wheat':'ghau gehun ઘઉં',
                  'Poha':'pauwa poha પૌંઆ',
                  'Sabudana':'sago સાબુદાણા',
                  'Bath soap':'sabun સાબુ',
                  'Agarbatti':'incense અગરબત્તી'}

# Example prices/images for a new store. All are editable by the shopkeeper.
SEED = [
 ('vegetables','Fresh potatoes','તાજા બટાકા',35,'1 kg','૧ કિલો','photo-1518977676601-b53f82aba655'),
 ('vegetables','Red onions','લાલ ડુંગળી',40,'1 kg','૧ કિલો','photo-1618512496248-a07fe83aa8cb'),
 ('vegetables','Fresh tomatoes','તાજા ટામેટાં',30,'1 kg','૧ કિલો','photo-1592924357228-91a4daadcfea'),
 ('vegetables','Green chillies','લીલા મરચાં',25,'250 g','૨૫૦ ગ્રામ','photo-1597362925123-77861d3fbac7'),
 ('grains','Sharbati wheat','શરબતી ઘઉં',420,'10 kg','૧૦ કિલો','photo-1574323347407-f5e1ad6d020b'),
 ('grains','Basmati rice','બાસમતી ચોખા',95,'1 kg','૧ કિલો','photo-1586201375761-83865001e31c'),
 ('pulses','Toor dal','તુવેર દાળ',155,'1 kg','૧ કિલો','photo-1708436477874-f6d1743504bc'),
 ('pulses','Kabuli chickpeas','કાબુલી ચણા',110,'1 kg','૧ કિલો','photo-1515543904379-3d757afe72e4'),
 ('pulses','Whole moong','આખા મગ',120,'1 kg','૧ કિલો','photo-1577110563838-e408b455c91d'),
 ('dairy','Fresh milk','તાજું દૂધ',34,'500 ml','૫૦૦ મિલી','photo-1550583724-b2692b85b150'),
 ('dairy','Desi ghee','દેશી ઘી',780,'1 L','૧ લિટર','photo-1631451095765-2c91616fc9e6'),
 ('oils','Groundnut oil','સીંગતેલ',2750,'15 kg tin','૧૫ કિલો ડબ્બો','photo-1474979266404-7eaacbcd87c5'),
 ('spices','Turmeric powder','હળદર પાવડર',75,'250 g','૨૫૦ ગ્રામ','photo-1615485290382-441e4d049cb5'),
 ('beverages','Strong tea','કડક ચા પત્તી',125,'250 g','૨૫૦ ગ્રામ','photo-1576092768241-dec231879fc3'),
 ('cleaning','Detergent powder','કપડાં ધોવાનો પાવડર',90,'1 kg','૧ કિલો','photo-1583947215259-38e31be8751f'),
 ('bath','Bath soap','નાહવાનો સાબુ',42,'1 piece','૧ નંગ','photo-1608571423902-eed4a5ad8108'),
 ('bath','Shampoo','શેમ્પૂ',125,'200 ml','૨૦૦ મિલી','photo-1608248543803-ba4f8c70ae0b'),
 ('bath','Toothpaste','ટૂથપેસ્ટ',65,'100 g','૧૦૦ ગ્રામ','photo-1607613009820-a29f7bb81c04'),
 ('puja','Incense sticks','અગરબત્તી',60,'1 pack','૧ પેકેટ','photo-1627769916425-74c2344a3439'),
]
LEGACY_ADDITIONS = [row for row in SEED if row[1] in
                    {'Kabuli chickpeas','Whole moong','Bath soap','Shampoo','Toothpaste'}]


def connect():
    if DATABASE_URL:
        global _pg_pool
        if _pg_pool is None:
            with _pool_lock:
                if _pg_pool is None:
                    from psycopg2.pool import ThreadedConnectionPool
                    _pg_pool = ThreadedConnectionPool(1, 8, DATABASE_URL)
        return _pg_pool.getconn(), True
    con = sqlite3.connect(os.environ.get('SQLITE_PATH', 'grocery.db'), timeout=10)
    con.execute('PRAGMA foreign_keys=ON')
    return con, False


def release(con, pg):
    if pg:
        con.rollback()  # close any read-only transaction before returning it
        _pg_pool.putconn(con)
    else:
        con.close()


def execute(sql, params=(), *, fetch=False, one=False, write=False):
    con, pg = connect()
    try:
        cur = con.cursor()
        cur.execute(sql if pg else sql.replace('%s', '?'), params)
        result = None
        if fetch or one:
            columns = [d[0] for d in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            result = (rows[0] if rows else None) if one else rows
        if write:
            con.commit()
            clear_cache()
        return result
    except Exception:
        con.rollback()
        raise
    finally:
        release(con, pg)


def init_db():
    con, pg = connect()
    try:
        cur = con.cursor()
        # A completed migration needs no DDL or demo-photo checks on every worker boot.
        try:
            cur.execute("SELECT value FROM settings WHERE key='schema_ready_v4'")
            if cur.fetchone():
                return
        except Exception as exc:
            missing_sqlite_table = (isinstance(exc, sqlite3.OperationalError)
                                    and 'no such table' in str(exc).lower())
            if not missing_sqlite_table and getattr(exc, 'pgcode', None) != '42P01':
                raise
            con.rollback()
        identity = 'SERIAL PRIMARY KEY' if pg else 'INTEGER PRIMARY KEY AUTOINCREMENT'
        binary = 'BYTEA' if pg else 'BLOB'
        cur.execute(f'''CREATE TABLE IF NOT EXISTS products (
            id {identity}, cat VARCHAR(50) NOT NULL,
            name_en VARCHAR(150) NOT NULL, name_gu VARCHAR(150) NOT NULL,
            price NUMERIC(10,2) NOT NULL, unit_en VARCHAR(50) NOT NULL,
            unit_gu VARCHAR(50) NOT NULL, in_stock BOOLEAN DEFAULT TRUE,
            image_url TEXT NOT NULL DEFAULT '', image_data {binary}, image_mime TEXT
        )''')
        if pg:
            cur.execute(f'ALTER TABLE products ADD COLUMN IF NOT EXISTS image_data {binary}')
            cur.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS image_mime TEXT')
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS subcategory_en VARCHAR(80) NOT NULL DEFAULT ''")
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS subcategory_gu VARCHAR(80) NOT NULL DEFAULT ''")
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS search_terms VARCHAR(300) NOT NULL DEFAULT ''")
            cur.execute('ALTER TABLE products ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT TRUE')
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS image_rev VARCHAR(20) NOT NULL DEFAULT ''")
        else:
            cur.execute('PRAGMA table_info(products)')
            columns = {row[1] for row in cur.fetchall()}
            if 'image_data' not in columns:
                cur.execute('ALTER TABLE products ADD COLUMN image_data BLOB')
            if 'image_mime' not in columns:
                cur.execute('ALTER TABLE products ADD COLUMN image_mime TEXT')
            for column, declaration in [('subcategory_en',"VARCHAR(80) NOT NULL DEFAULT ''"),
                                        ('subcategory_gu',"VARCHAR(80) NOT NULL DEFAULT ''"),
                                        ('search_terms',"VARCHAR(300) NOT NULL DEFAULT ''"),
                                        ('is_published','BOOLEAN NOT NULL DEFAULT TRUE')]:
                if column not in columns:
                    cur.execute(f'ALTER TABLE products ADD COLUMN {column} {declaration}')
            if 'image_rev' not in columns:
                cur.execute("ALTER TABLE products ADD COLUMN image_rev VARCHAR(20) NOT NULL DEFAULT ''")
        cur.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        cur.execute('SELECT COUNT(*) FROM products')
        empty = cur.fetchone()[0] == 0
        cur.execute("SELECT value FROM settings WHERE key='catalog_seed_v2'")
        already_migrated = cur.fetchone() is not None
        if empty or not already_migrated:
            query = '''INSERT INTO products
                (cat,name_en,name_gu,price,unit_en,unit_gu,in_stock,image_url)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
            for cat,en,gu,price,unit_en,unit_gu,photo in (SEED if empty else LEGACY_ADDITIONS):
                if not empty:
                    check = 'SELECT id FROM products WHERE name_en=%s'
                    cur.execute(check if pg else check.replace('%s','?'),(en,))
                    if cur.fetchone():
                        continue
                cur.execute(query if pg else query.replace('%s', '?'),
                            (cat,en,gu,price,unit_en,unit_gu,True,
                             f'https://images.unsplash.com/{photo}?w=420&auto=format&fit=crop&q=65'))
            marker = "INSERT INTO settings(key,value) VALUES('catalog_seed_v2','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value"
            cur.execute(marker)
        # Correct two repeated demo photos without touching merchant edits or uploads.
        demo_photo_fixes = (
            ('Toor dal', 'photo-1585994192701-f1a505c817ea', 'photo-1708436477874-f6d1743504bc'),
            ('Whole moong', 'photo-1515543904379-3d757afe72e4', 'photo-1577110563838-e408b455c91d'),
            ('Incense sticks', 'photo-1608571423902-eed4a5ad8108', 'photo-1627769916425-74c2344a3439'),
        )
        for name, previous, replacement in demo_photo_fixes:
            sql = '''UPDATE products SET image_url=%s WHERE name_en=%s AND image_url=%s
                     AND image_data IS NULL'''
            cur.execute(sql if pg else sql.replace('%s', '?'),
                        (f'https://images.unsplash.com/{replacement}?w=420&auto=format&fit=crop&q=65',
                         name, f'https://images.unsplash.com/{previous}?w=600&auto=format&fit=crop&q=80'))
        # Smaller demo thumbnails cut mobile image transfer; only exact demo URLs change.
        for _, name, _, _, _, _, photo in SEED:
            sql = '''UPDATE products SET image_url=%s WHERE name_en=%s AND image_url=%s
                     AND image_data IS NULL'''
            cur.execute(sql if pg else sql.replace('%s', '?'),
                        (f'https://images.unsplash.com/{photo}?w=420&auto=format&fit=crop&q=65',
                         name, f'https://images.unsplash.com/{photo}?w=600&auto=format&fit=crop&q=80'))
        cur.execute("SELECT value FROM settings WHERE key='taxonomy_seed_v1'")
        if cur.fetchone() is None:
            # Only legacy category identifiers are rewritten; prices and photos stay intact.
            for old_cat, new_cat in LEGACY_CATEGORY.items():
                sub_en = LEGACY_SUBCATEGORY[old_cat]
                sub_gu = dict(SUBCATEGORIES[new_cat])[sub_en]
                sql = '''UPDATE products SET cat=%s,subcategory_en=%s,subcategory_gu=%s
                         WHERE cat=%s AND subcategory_en=%s'''
                cur.execute(sql if pg else sql.replace('%s','?'),
                            (new_cat,sub_en,sub_gu,old_cat,''))
            for name, sub_en, sub_gu in [('Kabuli chickpeas','Beans & Peas','કઠોળ અને વટાણા'),
                                         ('Whole moong','Whole Pulses','આખા કઠોળ'),
                                         ('Fresh tomatoes','Staple Vegetables','રોજનાં શાક'),
                                         ('Shampoo','Hair Care','વાળની સંભાળ'),
                                         ('Toothpaste','Oral Care','દાંતની સંભાળ'),
                                         ('Desi ghee','Ghee & Fats','ઘી અને ચરબી'),
                                         ('Fresh milk','Milk','દૂધ')]:
                cat = next((key for key,groups in SUBCATEGORIES.items()
                            if (sub_en,sub_gu) in groups),None)
                if cat:
                    sql = '''UPDATE products SET cat=%s,subcategory_en=%s,subcategory_gu=%s
                             WHERE name_en=%s AND subcategory_en<>%s'''
                    cur.execute(sql if pg else sql.replace('%s','?'),
                                (cat,sub_en,sub_gu,name,sub_en))
            cur.execute("INSERT INTO settings(key,value) VALUES('taxonomy_seed_v1','1')")
        cur.execute(f'''CREATE TABLE IF NOT EXISTS product_variants (
            id {identity}, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            brand VARCHAR(80) NOT NULL DEFAULT '', unit_en VARCHAR(50) NOT NULL,
            unit_gu VARCHAR(50) NOT NULL, price NUMERIC(10,2) NOT NULL,
            compare_at_price NUMERIC(10,2), in_stock BOOLEAN NOT NULL DEFAULT TRUE,
            is_default BOOLEAN NOT NULL DEFAULT FALSE
        )''')
        cur.execute('''CREATE UNIQUE INDEX IF NOT EXISTS one_default_variant
                       ON product_variants(product_id) WHERE is_default=TRUE''')
        sql = '''INSERT INTO product_variants
                 (product_id,brand,unit_en,unit_gu,price,in_stock,is_default)
                 SELECT p.id,'',p.unit_en,p.unit_gu,p.price,p.in_stock,TRUE
                 FROM products p WHERE NOT EXISTS
                 (SELECT 1 FROM product_variants v WHERE v.product_id=p.id)
                 ON CONFLICT DO NOTHING'''
        cur.execute(sql)
        cur.execute(f'''CREATE TABLE IF NOT EXISTS orders (
            id {identity}, reference VARCHAR(32) NOT NULL UNIQUE,
            order_token VARCHAR(64) NOT NULL UNIQUE,
            customer_name VARCHAR(100) NOT NULL, phone VARCHAR(20) NOT NULL,
            fulfillment VARCHAR(12) NOT NULL, address VARCHAR(300) NOT NULL DEFAULT '',
            pincode VARCHAR(6) NOT NULL DEFAULT '', note VARCHAR(500) NOT NULL DEFAULT '',
            items_json TEXT NOT NULL, subtotal NUMERIC(10,2) NOT NULL,
            delivery_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
            total NUMERIC(10,2) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'new',
            created_at VARCHAR(32) NOT NULL
        )''')
        cur.execute('CREATE INDEX IF NOT EXISTS orders_created ON orders(id)')
        cur.execute("INSERT INTO settings(key,value) VALUES('schema_ready_v4','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        release(con, pg)


def _read_settings():
    values = {'shop_name': os.environ.get('SHOP_NAME', 'Ved Grocery Mart'),
              'phone': os.environ.get('STORE_PHONE', '9979215875'),
              'whatsapp': os.environ.get('WHATSAPP_PHONE', '919979215875'),
              'pickup_enabled': '1', 'delivery_enabled': '0',
              'pickup_address': '', 'opening_hours': '9:00 AM – 9:00 PM',
              'delivery_pincodes': '', 'delivery_fee': '0',
              'minimum_order': '0'}
    for row in execute('SELECT key,value FROM settings', fetch=True):
        if row['key'] in values:
            values[row['key']] = row['value']
    values['phone_link'] = re.sub(r'[^+\d]', '', values['phone'])
    values['wa_digits'] = re.sub(r'\D', '', values['whatsapp'])
    return values


def settings():
    return cached('shop_settings', _read_settings)


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']


app.jinja_env.globals['csrf_token'] = csrf_token


def order_token():
    if 'order_token' not in session:
        session['order_token'] = secrets.token_urlsafe(24)
    return session['order_token']


app.jinja_env.globals['order_token'] = order_token


def require_csrf():
    supplied = request.form.get('csrf', '')
    if not supplied or not hmac.compare_digest(session.get('csrf', ''), supplied):
        abort(403)


def admin_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        if request.method == 'POST':
            require_csrf()
        return fn(*args, **kwargs)
    return decorated


def valid_image(file):
    if not file or not file.filename:
        return None
    data = file.read(3_000_001)
    if not 100 <= len(data) <= 3_000_000:
        raise ValueError('Image must be under 3 MB.')
    if not (data.startswith(b'\xff\xd8\xff') or
            data.startswith(b'\x89PNG\r\n\x1a\n') or
            (data[:4] == b'RIFF' and data[8:12] == b'WEBP')):
        raise ValueError('Upload a JPG, PNG or WebP image.')
    # Normalize phone photos before storing them in PostgreSQL.
    from PIL import Image, ImageOps, UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(data)) as original:
            if original.width * original.height > 30_000_000:
                raise ValueError('Image dimensions are too large.')
            frame = ImageOps.exif_transpose(original)
            frame.thumbnail((720, 720))
            frame = frame.convert('RGBA' if 'A' in frame.getbands() else 'RGB')
            result = io.BytesIO()
            frame.save(result, format='WEBP', quality=78, method=4)
        return result.getvalue(), 'image/webp'
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError('The image could not be read. Try another JPG, PNG or WebP.') from exc


def variant_payload(row):
    return dict(id=row['id'], product_id=row['product_id'], brand=row['brand'],
                unit_en=row['unit_en'], unit_gu=row['unit_gu'],
                price=float(row['price']),
                compare_at_price=float(row['compare_at_price']) if row['compare_at_price'] is not None else None,
                in_stock=bool(row['in_stock']), is_default=bool(row['is_default']))


def product_payload(row, variants):
    available = [v for v in variants if v['in_stock']]
    featured = min(available or variants, key=lambda v: v['price']) if variants else None
    default = next((v for v in variants if v['is_default']), featured)
    return dict(id=row['id'], cat=row['cat'], name_en=row['name_en'],
                name_gu=row['name_gu'], price=featured['price'] if featured else float(row['price']),
                subcategory_en=row['subcategory_en'], subcategory_gu=row['subcategory_gu'],
                search_terms=row['search_terms'], is_published=bool(row['is_published']),
                unit_en=featured['unit_en'] if featured else row['unit_en'],
                unit_gu=featured['unit_gu'] if featured else row['unit_gu'],
                in_stock=bool(available), variants=variants,
                featured_variant_id=featured['id'] if featured else None,
                default_variant=default,
                brands=sorted({v['brand'] for v in variants if v['brand']}),
                on_offer=any(v['compare_at_price'] and v['compare_at_price'] > v['price']
                             for v in available),
                image_url=url_for('product_image', item_id=row['id'],
                                  v=row['image_rev'] or 'initial')
                if row.get('has_image') else row['image_url'],
                has_upload=bool(row.get('has_image')),
                fallback_url=url_for('static', filename='fallback.svg'))


def _read_products():
    # One DB round-trip for the catalog, important when Railway services are far apart.
    joined = execute('''SELECT p.id,p.cat,p.name_en,p.name_gu,p.subcategory_en,
                        p.subcategory_gu,p.search_terms,p.is_published,p.price,
                        p.unit_en,p.unit_gu,p.in_stock,p.image_url,p.image_rev,
                        (p.image_data IS NOT NULL) AS has_image,
                        v.id AS variant_id,v.product_id,v.brand,
                        v.unit_en AS variant_unit_en,v.unit_gu AS variant_unit_gu,
                        v.price AS variant_price,v.compare_at_price,
                        v.in_stock AS variant_in_stock,v.is_default
                        FROM products p LEFT JOIN product_variants v ON v.product_id=p.id
                        ORDER BY p.id,v.is_default DESC,v.id''', fetch=True)
    products = {}
    by_product = {}
    for row in joined:
        products.setdefault(row['id'], row)
        if row['variant_id'] is not None:
            variant = dict(id=row['variant_id'], product_id=row['product_id'],
                           brand=row['brand'], unit_en=row['variant_unit_en'],
                           unit_gu=row['variant_unit_gu'], price=row['variant_price'],
                           compare_at_price=row['compare_at_price'],
                           in_stock=row['variant_in_stock'],is_default=row['is_default'])
            by_product.setdefault(row['id'], []).append(variant_payload(variant))
    return [product_payload(row, by_product.get(item_id, []))
            for item_id,row in products.items()]


def all_products():
    return cached('products', _read_products)


@app.context_processor
def context():
    return {'shop': settings(), 'categories': CATEGORIES, 'subcategories': SUBCATEGORIES,
            'is_admin': bool(session.get('admin'))}


@app.get('/')
def home():
    lang = request.args.get('lang', 'gu')
    lang = lang if lang in ('gu','en') else 'gu'
    category = request.args.get('cat', 'all')
    category = category if category in CATEGORY_IDS else 'all'
    subcategory = request.args.get('sub', '').strip()[:80]
    if category == 'all' or subcategory not in {s[0] for s in SUBCATEGORIES[category]}:
        subcategory = ''
    query = request.args.get('q', '').strip()[:80]
    brand = request.args.get('brand', '').strip()[:80]
    max_price = request.args.get('max_price', '').strip()
    try:
        price_limit = float(max_price) if max_price else None
    except ValueError:
        price_limit = None
    in_stock_only = request.args.get('stock') == '1'
    offers_only = request.args.get('offers') == '1'
    sort = request.args.get('sort', 'default')
    all_items = [p for p in all_products() if p['is_published']]
    visible = [p for p in all_items if (category == 'all' or p['cat'] == category)
               and (not subcategory or p['subcategory_en'] == subcategory)
               and (not query or all(token in (' '.join((p['name_en'],p['name_gu'],
                    p['subcategory_en'],p['subcategory_gu'],p['search_terms'],
                    SEARCH_ALIASES.get(p['name_en'],''),
                    ' '.join(v['brand'] for v in p['variants'])))).casefold()
                    for token in query.casefold().split()))
               and (not brand or brand in p['brands'])
               and (price_limit is None or p['price'] <= price_limit)
               and (not in_stock_only or p['in_stock'])
               and (not offers_only or p['on_offer'])]
    if sort in ('price_asc', 'price_desc'):
        visible.sort(key=lambda p: p['price'], reverse=sort == 'price_desc')
    return render_template('catalog.html', products=visible, all_items=all_items,
                           category=category, subcategory=subcategory, query=query, lang=lang,
                           brand=brand, max_price=max_price, stock=in_stock_only,
                           offers=offers_only, sort=sort,
                           brands=sorted({v['brand'] for p in all_items for v in p['variants'] if v['brand']}),
                           category_labels={id:(gu,en) for id,en,gu,_ in CATEGORIES})


@app.get('/api/products')
def public_products():
    return jsonify([p for p in all_products() if p['is_published']])


@app.get('/healthz')
def healthz():
    return jsonify(ok=True)


@app.get('/service-worker.js')
def service_worker():
    response = send_file('static/service-worker.js', mimetype='application/javascript')
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


ORDER_ATTEMPTS = {}
_order_attempt_lock = threading.Lock()
ORDER_STATUSES = ('new', 'confirmed', 'ready', 'delivered', 'cancelled')


def order_error(message, status=400):
    return jsonify(error=message), status


@app.post('/api/orders')
def create_order():
    require_csrf()
    if request.form.get('website'):
        return order_error('Unable to submit this request.')
    token = request.form.get('order_token','')
    if not token or not hmac.compare_digest(session.get('order_token',''),token):
        return order_error('Refresh the page and try again.')
    # A browser retry with the same token returns the existing request.
    existing = execute('SELECT reference FROM orders WHERE order_token=%s',(token,),one=True)
    if existing:
        return jsonify(reference=existing['reference'],
                       url=url_for('order_receipt',reference=existing['reference']))
    ip = request.remote_addr or 'unknown'
    with _order_attempt_lock:
        now = time.monotonic()
        attempts = [stamp for stamp in ORDER_ATTEMPTS.get(ip, []) if now-stamp < 900]
        if len(attempts) >= 8:
            return order_error('Please call the shop to place more requests.',429)
        attempts.append(now)
        ORDER_ATTEMPTS[ip] = attempts
        if len(ORDER_ATTEMPTS) > 2000:
            ORDER_ATTEMPTS.clear()
    name = request.form.get('customer_name','').strip()[:100]
    phone = re.sub(r'\D','',request.form.get('phone',''))
    mode = request.form.get('fulfillment','')
    address = request.form.get('address','').strip()[:300]
    pincode = request.form.get('pincode','').strip()
    note = request.form.get('note','').strip()[:500]
    substitution = request.form.get('substitution','call')
    if substitution not in ('call','none'):
        return order_error('Choose a substitution preference.')
    preference = ('Call before replacing unavailable items' if substitution == 'call'
                  else 'Do not substitute unavailable items')
    note = (preference + (' · ' + note if note else ''))[:500]
    shop = settings()
    if len(name) < 2 or not 10 <= len(phone) <= 15:
        return order_error('Enter your name and a valid mobile number.')
    if mode == 'delivery':
        allowed = {x.strip() for x in shop['delivery_pincodes'].split(',') if x.strip()}
        if shop['delivery_enabled'] != '1' or pincode not in allowed or len(address) < 10:
            return order_error('Enter a delivery address and one of the listed service pincodes.')
    elif mode == 'pickup':
        if shop['pickup_enabled'] != '1':
            return order_error('Pickup is currently unavailable.')
        address,pincode = '',''
    else:
        return order_error('Choose delivery or shop pickup.')
    try:
        submitted = json.loads(request.form.get('cart_json',''))
    except (ValueError, TypeError):
        return order_error('Your shopping list could not be read.')
    if not isinstance(submitted,list) or not 1 <= len(submitted) <= 100:
        return order_error('Add at least one item to your list.')
    # Checkout reads current database values, even if the public catalog cache is warm.
    variants = {v['id']:(p,v) for p in _read_products() if p['is_published']
                for v in p['variants']}
    lines = []
    subtotal = Decimal('0')
    seen = set()
    for entry in submitted:
        if (not isinstance(entry,dict) or type(entry.get('id')) is not int or
                type(entry.get('qty')) is not int):
            return order_error('The shopping list contains an invalid item.')
        vid,qty = entry['id'],entry['qty']
        if vid in seen or not 1 <= qty <= 99 or vid not in variants:
            return order_error('Refresh your list and try again.')
        seen.add(vid)
        product,variant = variants[vid]
        if not variant['in_stock']:
            return order_error(f"{product['name_en']} is currently unavailable. Refresh the page.")
        amount = Decimal(str(variant['price']))
        subtotal += amount * qty
        lines.append(dict(variant_id=vid,product_id=product['id'],
                          name_en=product['name_en'],name_gu=product['name_gu'],
                          brand=variant['brand'],unit_en=variant['unit_en'],
                          unit_gu=variant['unit_gu'],price=float(amount),qty=qty))
    if subtotal < Decimal(shop['minimum_order']):
        return order_error(f"Minimum order is ₹{shop['minimum_order']}.")
    fee = Decimal(shop['delivery_fee']) if mode == 'delivery' else Decimal('0')
    reference = 'VG' + datetime.now(timezone.utc).strftime('%Y%m%d') + secrets.token_hex(6).upper()
    created = datetime.now(timezone.utc).isoformat(timespec='seconds')
    sql = '''INSERT INTO orders
             (reference,order_token,customer_name,phone,fulfillment,address,pincode,
              note,items_json,subtotal,delivery_fee,total,status,created_at)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'new',%s)
             ON CONFLICT(order_token) DO NOTHING'''
    execute(sql,(reference,token,name,phone,mode,address,pincode,note,
                 json.dumps(lines,ensure_ascii=False),str(subtotal),str(fee),
                 str(subtotal+fee),created),write=True)
    stored = execute('SELECT reference FROM orders WHERE order_token=%s',(token,),one=True)
    session['order_token'] = secrets.token_urlsafe(24)
    return jsonify(reference=stored['reference'],
                   url=url_for('order_receipt',reference=stored['reference']))


@app.get('/order/<reference>')
def order_receipt(reference):
    if not re.fullmatch(r'VG\d{8}[A-F0-9]{12}', reference):
        abort(404)
    row = execute('''SELECT reference,items_json,subtotal,delivery_fee,total,
                     fulfillment,status,created_at FROM orders WHERE reference=%s''',
                  (reference,),one=True)
    if not row:
        abort(404)
    response = app.make_response(render_template('order.html', order=dict(
        row, items=json.loads(row['items_json']), subtotal=float(row['subtotal']),
        delivery_fee=float(row['delivery_fee']), total=float(row['total']))))
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@app.get('/image/<int:item_id>')
def product_image(item_id):
    revision = request.args.get('v','')[:20]
    row = cached(('image', item_id, revision),
                 lambda: execute('SELECT image_data,image_mime FROM products WHERE id=%s',
                                 (item_id,), one=True), ttl=120)
    if not row or not row['image_data']:
        abort(404)
    data = bytes(row['image_data'])
    response = send_file(io.BytesIO(data), mimetype=row['image_mime'] or 'application/octet-stream')
    response.headers['Cache-Control'] = 'public, max-age=604800'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.get('/placeholder/<int:item_id>.svg')
def product_fallback(item_id):
    row = cached(('placeholder', item_id),
                 lambda: execute('SELECT name_en,cat FROM products WHERE id=%s',
                                 (item_id,), one=True), ttl=120)
    if not row:
        abort(404)
    name = html.escape(row['name_en'][:28])
    initials = html.escape(''.join(word[:1] for word in row['name_en'].split()[:2]).upper())
    category = html.escape(row['cat'].upper())
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 430">
      <defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#245571"/><stop offset="1" stop-color="#102637"/></linearGradient></defs>
      <rect width="600" height="430" fill="url(#g)"/><circle cx="300" cy="193" r="115" fill="#397c95" opacity=".32"/>
      <circle cx="300" cy="193" r="89" fill="#3b83a0" opacity=".48"/>
      <text x="300" y="219" text-anchor="middle" fill="#c9f4f7" font-family="monospace" font-size="69" font-weight="bold">{initials}</text>
      <text x="300" y="350" text-anchor="middle" fill="#d7f0f7" font-family="monospace" font-size="22">{name}</text>
      <text x="300" y="385" text-anchor="middle" fill="#84b7ca" font-family="monospace" font-size="16">{category}</text>
    </svg>'''
    return app.response_class(svg, mimetype='image/svg+xml')


FAILED_LOGINS = {}


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        require_csrf()
        key = request.remote_addr or 'unknown'
        now = time.monotonic()
        count, reset = FAILED_LOGINS.get(key, (0, now + 900))
        if reset < now:
            count, reset = 0, now + 900
        if count >= 8:
            return render_template('login.html', error='Please try again in 15 minutes.'), 429
        username = request.form.get('username', '')[:100]
        password = request.form.get('password', '')[:1000]
        try:
            match = bool(ADMIN_PASSWORD_HASH) and username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password)
        except ValueError:
            match = False
        if match:
            FAILED_LOGINS.pop(key, None)
            session.clear()
            session['admin'] = True
            session.permanent = True
            csrf_token()
            return redirect(url_for('admin'))
        FAILED_LOGINS[key] = (count + 1, reset)
        return render_template('login.html', error='Incorrect username or password.'), 401
    return render_template('login.html', error=None)


@app.post('/logout')
@admin_required
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.get('/admin')
@admin_required
def admin():
    products = all_products()
    grouped = [(cat, en, gu, icon, [p for p in products if p['cat'] == cat])
               for cat, en, gu, icon in CATEGORIES if cat != 'all']
    rows = execute('''SELECT id,reference,customer_name,phone,fulfillment,address,
                      pincode,note,items_json,subtotal,delivery_fee,total,status,created_at
                      FROM orders ORDER BY id DESC LIMIT 100''', fetch=True)
    orders = [dict(row, items=json.loads(row['items_json']),
                   subtotal=float(row['subtotal']), delivery_fee=float(row['delivery_fee']),
                   total=float(row['total'])) for row in rows]
    active_names = {p['name_en'].casefold() for p in products}
    suggestions = {key: [(sub_en,sub_gu,[(en,gu) for cat,s,g,en,gu in TEMPLATES
                            if cat == key and s == sub_en and en.casefold() not in active_names])
                         for sub_en,sub_gu in SUBCATEGORIES[key]] for key in CATEGORY_IDS}
    return render_template('admin.html', products=products, grouped=grouped,
                           suggestions=suggestions, orders=orders)


def form_product():
    cat = request.form.get('cat', '')
    sub_en = request.form.get('subcategory_en','').strip()[:80]
    if cat not in CATEGORY_IDS or sub_en not in {s[0] for s in SUBCATEGORIES[cat]}:
        raise ValueError('Choose a valid category and subcategory.')
    sub_gu = dict(SUBCATEGORIES[cat])[sub_en]
    name_en = request.form.get('name_en', '').strip()[:150]
    name_gu = request.form.get('name_gu', '').strip()[:150]
    unit_en = request.form.get('unit_en', '').strip()[:50]
    unit_gu = request.form.get('unit_gu', '').strip()[:50]
    price = request.form.get('price', '').strip()
    if cat not in CATEGORY_IDS or min(len(name_en),len(name_gu),len(unit_en),len(unit_gu)) < 1:
        raise ValueError('Complete the item name, unit and category in both languages.')
    try:
        amount = float(price)
    except ValueError as exc:
        raise ValueError('Enter a valid price.') from exc
    if not 0 <= amount <= 100000 or not amount == amount:
        raise ValueError('Price must be between ₹0 and ₹100,000.')
    image_url = request.form.get('image_url','').strip()[:1000]
    if image_url and (urlparse(image_url).scheme != 'https' or not urlparse(image_url).netloc):
        raise ValueError('Image link must start with https://')
    photo = valid_image(request.files.get('image_file'))
    terms = request.form.get('search_terms','').strip()[:300]
    return (cat,sub_en,sub_gu,name_en,name_gu,round(amount,2),unit_en,unit_gu,
            request.form.get('in_stock') == 'on',image_url,photo,terms)


@app.post('/admin/add')
@admin_required
def add_product():
    try:
        cat,sub_en,sub_gu,en,gu,price,unit_en,unit_gu,stock,image,photo,terms = form_product()
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin'))
    if not photo and not image:
        flash('Add a photo upload or HTTPS photo link for the new item.', 'error')
        return redirect(url_for('admin') + '#add-item')
    binary,mime = photo if photo else (None,None)
    brand = request.form.get('brand', '').strip()[:80]
    con, pg = connect()
    try:
        cur = con.cursor()
        sql = '''INSERT INTO products (cat,subcategory_en,subcategory_gu,name_en,name_gu,
                 price,unit_en,unit_gu,in_stock,image_url,image_data,image_mime,search_terms,image_rev)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        cur.execute(sql + (' RETURNING id' if pg else '') if pg else sql.replace('%s','?'),
                    (cat,sub_en,sub_gu,en,gu,price,unit_en,unit_gu,stock,image,binary,mime,terms,
                     secrets.token_hex(8) if photo else ''))
        item_id = cur.fetchone()[0] if pg else cur.lastrowid
        sql = '''INSERT INTO product_variants
                 (product_id,brand,unit_en,unit_gu,price,in_stock,is_default)
                 VALUES (%s,%s,%s,%s,%s,%s,TRUE)'''
        cur.execute(sql if pg else sql.replace('%s','?'),
                    (item_id,brand,unit_en,unit_gu,price,stock))
        con.commit()
        clear_cache()
    except Exception:
        con.rollback()
        raise
    finally:
        release(con, pg)
    flash('Item added. Customers can see it now.', 'success')
    return redirect(url_for('admin'))


@app.post('/admin/item/<int:item_id>')
@admin_required
def update_product(item_id):
    if not execute('SELECT id FROM products WHERE id=%s',(item_id,),one=True):
        abort(404)
    try:
        cat,sub_en,sub_gu,en,gu,price,unit_en,unit_gu,stock,image,photo,terms = form_product()
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin'))
    if photo:
        execute('''UPDATE products SET cat=%s,subcategory_en=%s,subcategory_gu=%s,
                    search_terms=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url=%s,
                    image_data=%s,image_mime=%s,image_rev=%s WHERE id=%s''',
                (cat,sub_en,sub_gu,terms,en,gu,price,unit_en,unit_gu,stock,image,*photo,
                 secrets.token_hex(8),item_id),write=True)
    elif request.form.get('remove_photo') == 'on':
        execute('''UPDATE products SET cat=%s,subcategory_en=%s,subcategory_gu=%s,
                    search_terms=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url='',
                    image_data=NULL,image_mime=NULL WHERE id=%s''',
                (cat,sub_en,sub_gu,terms,en,gu,price,unit_en,unit_gu,stock,item_id),write=True)
    elif image:
        execute('''UPDATE products SET cat=%s,subcategory_en=%s,subcategory_gu=%s,
                    search_terms=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url=%s,
                    image_data=NULL,image_mime=NULL WHERE id=%s''',
                (cat,sub_en,sub_gu,terms,en,gu,price,unit_en,unit_gu,stock,image,item_id),write=True)
    else:
        execute('''UPDATE products SET cat=%s,subcategory_en=%s,subcategory_gu=%s,
                    search_terms=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url=%s WHERE id=%s''',
                (cat,sub_en,sub_gu,terms,en,gu,price,unit_en,unit_gu,stock,image,item_id),write=True)
    execute('''UPDATE product_variants SET price=%s,unit_en=%s,unit_gu=%s,
               in_stock=%s WHERE product_id=%s AND is_default=TRUE''',
            (price,unit_en,unit_gu,stock,item_id),write=True)
    flash('Item updated. The public catalog now shows the new details.', 'success')
    return redirect(url_for('admin') + f'#item-{item_id}')


@app.post('/admin/delete/<int:item_id>')
@admin_required
def delete_product(item_id):
    execute('DELETE FROM products WHERE id=%s',(item_id,),write=True)
    flash('Item deleted.', 'success')
    return redirect(url_for('admin'))


@app.post('/admin/quick/<int:variant_id>')
@admin_required
def quick_price(variant_id):
    row = execute('SELECT id,product_id,is_default FROM product_variants WHERE id=%s',
                  (variant_id,),one=True)
    if not row:
        abort(404)
    try:
        price = Decimal(request.form.get('price',''))
        if not price.is_finite() or not 0 <= price <= 100000 or price.as_tuple().exponent < -2:
            raise ValueError
    except Exception:
        flash('Enter a valid price with up to two decimal places.', 'error')
        return redirect(url_for('admin') + '#daily-prices')
    stock = request.form.get('in_stock') == 'on'
    con, pg = connect()
    try:
        cur = con.cursor()
        sql = 'UPDATE product_variants SET price=%s,in_stock=%s WHERE id=%s'
        cur.execute(sql if pg else sql.replace('%s','?'),(str(price),stock,variant_id))
        if row['is_default']:
            sql = 'UPDATE products SET price=%s,in_stock=%s WHERE id=%s'
            cur.execute(sql if pg else sql.replace('%s','?'),
                        (str(price),stock,row['product_id']))
        con.commit()
        clear_cache()
    except Exception:
        con.rollback()
        raise
    finally:
        release(con,pg)
    flash('Price and availability saved.', 'success')
    return redirect(url_for('admin') + '#daily-prices')


@app.post('/admin/item/<int:item_id>/visibility')
@admin_required
def product_visibility(item_id):
    published = request.form.get('is_published') == '1'
    if not execute('SELECT id FROM products WHERE id=%s',(item_id,),one=True):
        abort(404)
    execute('UPDATE products SET is_published=%s WHERE id=%s',
            (published,item_id),write=True)
    flash('Product is now visible to customers.' if published else
          'Product hidden from customers. Existing requests remain saved.', 'success')
    return redirect(url_for('admin') + f'#item-{item_id}')


def variant_form():
    brand = request.form.get('brand','').strip()[:80]
    unit_en = request.form.get('unit_en','').strip()[:50]
    unit_gu = request.form.get('unit_gu','').strip()[:50]
    if not unit_en or not unit_gu:
        raise ValueError('Enter the pack size in both languages.')
    try:
        price = round(float(request.form.get('price','')), 2)
        old_text = request.form.get('compare_at_price','').strip()
        old = round(float(old_text), 2) if old_text else None
    except ValueError as exc:
        raise ValueError('Enter valid prices.') from exc
    if not 0 <= price <= 100000 or price != price or (old is not None and
            (old <= price or old > 100000 or old != old)):
        raise ValueError('Offer price must be lower than the regular price.')
    return brand,unit_en,unit_gu,price,old,request.form.get('in_stock') == 'on'


@app.post('/admin/item/<int:item_id>/variant')
@admin_required
def add_variant(item_id):
    if not execute('SELECT id FROM products WHERE id=%s',(item_id,),one=True):
        abort(404)
    try:
        values = variant_form()
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin') + f'#item-{item_id}')
    execute('''INSERT INTO product_variants
               (product_id,brand,unit_en,unit_gu,price,compare_at_price,in_stock)
               VALUES (%s,%s,%s,%s,%s,%s,%s)''',(item_id,*values),write=True)
    flash('Pack size added.', 'success')
    return redirect(url_for('admin') + f'#item-{item_id}')


@app.post('/admin/variant/<int:variant_id>')
@admin_required
def update_variant(variant_id):
    row = execute('SELECT id,product_id,is_default FROM product_variants WHERE id=%s',
                  (variant_id,),one=True)
    if not row:
        abort(404)
    try:
        brand,unit_en,unit_gu,price,old,stock = variant_form()
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin') + f"#item-{row['product_id']}")
    execute('''UPDATE product_variants SET brand=%s,unit_en=%s,unit_gu=%s,
               price=%s,compare_at_price=%s,in_stock=%s WHERE id=%s''',
            (brand,unit_en,unit_gu,price,old,stock,variant_id),write=True)
    if row['is_default']:
        execute('''UPDATE products SET unit_en=%s,unit_gu=%s,price=%s,in_stock=%s
                   WHERE id=%s''',(unit_en,unit_gu,price,stock,row['product_id']),write=True)
    flash('Pack size updated.', 'success')
    return redirect(url_for('admin') + f"#item-{row['product_id']}")


@app.post('/admin/variant/<int:variant_id>/delete')
@admin_required
def delete_variant(variant_id):
    row = execute('SELECT id,product_id,is_default FROM product_variants WHERE id=%s',
                  (variant_id,),one=True)
    if not row:
        abort(404)
    if row['is_default']:
        flash('The original pack size cannot be removed. Edit it or delete the product.', 'error')
    else:
        execute('DELETE FROM product_variants WHERE id=%s',(variant_id,),write=True)
        flash('Pack size removed.', 'success')
    return redirect(url_for('admin') + f"#item-{row['product_id']}")


@app.post('/admin/settings')
@admin_required
def update_settings():
    name = request.form.get('shop_name','').strip()[:80]
    phone = request.form.get('phone','').strip()[:22]
    whatsapp = re.sub(r'\D','',request.form.get('whatsapp',''))
    if not name or not 8 <= len(re.sub(r'\D','',phone)) <= 15 or not 8 <= len(whatsapp) <= 15:
        flash('Enter a shop name and valid call and WhatsApp numbers.', 'error')
        return redirect(url_for('admin'))
    pincodes = re.split(r'[\s,]+',request.form.get('delivery_pincodes','').strip())
    pincodes = sorted({p for p in pincodes if p})
    delivery = request.form.get('delivery_enabled') == 'on'
    pickup = request.form.get('pickup_enabled') == 'on'
    if ((not pickup and not delivery) or
            any(not re.fullmatch(r'\d{6}', p) for p in pincodes) or
            (delivery and not pincodes)):
        flash('Enable pickup or delivery. Delivery needs valid six-digit pincodes.', 'error')
        return redirect(url_for('admin'))
    try:
        fee = Decimal(request.form.get('delivery_fee','0'))
        minimum = Decimal(request.form.get('minimum_order','0'))
    except Exception:
        flash('Enter valid delivery and minimum order amounts.', 'error')
        return redirect(url_for('admin'))
    if not all(x.is_finite() and 0 <= x <= 10000 for x in (fee,minimum)):
        flash('Delivery and minimum order amounts must be between ₹0 and ₹10,000.', 'error')
        return redirect(url_for('admin'))
    address = request.form.get('pickup_address','').strip()[:250]
    hours = request.form.get('opening_hours','').strip()[:100]
    con, pg = connect()
    try:
        cur = con.cursor()
        sql = '''INSERT INTO settings (key,value) VALUES (%s,%s)
                 ON CONFLICT(key) DO UPDATE SET value=excluded.value'''
        values = [('shop_name',name),('phone',phone),('whatsapp',whatsapp),
                  ('pickup_enabled','1' if pickup else '0'),
                  ('delivery_enabled','1' if delivery else '0'),
                  ('pickup_address',address),('opening_hours',hours),
                  ('delivery_pincodes',','.join(pincodes)),
                  ('delivery_fee',str(fee)),('minimum_order',str(minimum))]
        for key,value in values:
            cur.execute(sql if pg else sql.replace('%s','?'), (key,value))
        con.commit()
        clear_cache()
    except Exception:
        con.rollback()
        raise
    finally:
        release(con, pg)
    flash('Shop details saved.', 'success')
    return redirect(url_for('admin'))


@app.post('/admin/order/<int:order_id>/status')
@admin_required
def update_order_status(order_id):
    status = request.form.get('status','')
    if status not in ORDER_STATUSES:
        abort(400)
    if not execute('SELECT id FROM orders WHERE id=%s',(order_id,),one=True):
        abort(404)
    execute('UPDATE orders SET status=%s WHERE id=%s',(status,order_id),write=True)
    flash('Order request updated.', 'success')
    return redirect(url_for('admin') + '#orders')


for attempt in range(10):
    try:
        init_db()
        break
    except Exception as exc:
        if attempt == 9 or not DATABASE_URL:
            raise
        app.logger.warning('Database not ready (%s); retrying in 2 seconds.', exc)
        time.sleep(2)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=False)
