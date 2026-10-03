"""Public grocery catalog and private shopkeeper dashboard for Railway."""
import hmac
import html
import io
import os
import re
import secrets
import sqlite3
import time
from datetime import timedelta
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, send_file, session, url_for)
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=bool(os.environ.get('RAILWAY_ENVIRONMENT_ID')),
)
DATABASE_URL = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://', 1)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')
if os.environ.get('RAILWAY_ENVIRONMENT_ID') and not all((DATABASE_URL, os.environ.get('SECRET_KEY'), ADMIN_PASSWORD_HASH)):
    raise RuntimeError('Railway requires DATABASE_URL, SECRET_KEY and ADMIN_PASSWORD_HASH.')

CATEGORIES = [
    ('all', 'All items', 'બધી વસ્તુઓ', '▦'),
    ('vegetables', 'Vegetables', 'શાકભાજી', '🥬'),
    ('grains', 'Grains & flour', 'અનાજ અને લોટ', '🌾'),
    ('pulses', 'Dal & pulses', 'દાળ અને કઠોળ', '🫘'),
    ('dairy', 'Milk & ghee', 'દૂધ અને ઘી', '🥛'),
    ('oils', 'Cooking oils', 'ખાદ્ય તેલ', '🫙'),
    ('spices', 'Spices', 'મસાલા', '🌶️'),
    ('beverages', 'Tea & snacks', 'ચા અને નાસ્તો', '☕'),
    ('cleaning', 'Daily essentials', 'દૈનિક જરૂરિયાત', '🧴'),
    ('bath', 'Bath & care', 'બાથરૂમ સામાન', '🧼'),
    ('puja', 'Puja essentials', 'પૂજા સામગ્રી', '🪔'),
]
CATEGORY_IDS = {c[0] for c in CATEGORIES if c[0] != 'all'}

# Example prices/images for a new store. All are editable by the shopkeeper.
SEED = [
 ('vegetables','Fresh potatoes','તાજા બટાકા',35,'1 kg','૧ કિલો','photo-1518977676601-b53f82aba655'),
 ('vegetables','Red onions','લાલ ડુંગળી',40,'1 kg','૧ કિલો','photo-1618512496248-a07fe83aa8cb'),
 ('vegetables','Fresh tomatoes','તાજા ટામેટાં',30,'1 kg','૧ કિલો','photo-1592924357228-91a4daadcfea'),
 ('vegetables','Green chillies','લીલા મરચાં',25,'250 g','૨૫૦ ગ્રામ','photo-1597362925123-77861d3fbac7'),
 ('grains','Sharbati wheat','શરબતી ઘઉં',420,'10 kg','૧૦ કિલો','photo-1574323347407-f5e1ad6d020b'),
 ('grains','Basmati rice','બાસમતી ચોખા',95,'1 kg','૧ કિલો','photo-1586201375761-83865001e31c'),
 ('pulses','Toor dal','તુવેર દાળ',155,'1 kg','૧ કિલો','photo-1585994192701-f1a505c817ea'),
 ('pulses','Kabuli chickpeas','કાબુલી ચણા',110,'1 kg','૧ કિલો','photo-1515543904379-3d757afe72e4'),
 ('pulses','Whole moong','આખા મગ',120,'1 kg','૧ કિલો','photo-1515543904379-3d757afe72e4'),
 ('dairy','Fresh milk','તાજું દૂધ',34,'500 ml','૫૦૦ મિલી','photo-1550583724-b2692b85b150'),
 ('dairy','Desi ghee','દેશી ઘી',780,'1 L','૧ લિટર','photo-1631451095765-2c91616fc9e6'),
 ('oils','Groundnut oil','સીંગતેલ',2750,'15 kg tin','૧૫ કિલો ડબ્બો','photo-1474979266404-7eaacbcd87c5'),
 ('spices','Turmeric powder','હળદર પાવડર',75,'250 g','૨૫૦ ગ્રામ','photo-1615485290382-441e4d049cb5'),
 ('beverages','Strong tea','કડક ચા પત્તી',125,'250 g','૨૫૦ ગ્રામ','photo-1576092768241-dec231879fc3'),
 ('cleaning','Detergent powder','કપડાં ધોવાનો પાવડર',90,'1 kg','૧ કિલો','photo-1583947215259-38e31be8751f'),
 ('bath','Bath soap','નાહવાનો સાબુ',42,'1 piece','૧ નંગ','photo-1608571423902-eed4a5ad8108'),
 ('bath','Shampoo','શેમ્પૂ',125,'200 ml','૨૦૦ મિલી','photo-1608248543803-ba4f8c70ae0b'),
 ('bath','Toothpaste','ટૂથપેસ્ટ',65,'100 g','૧૦૦ ગ્રામ','photo-1607613009820-a29f7bb81c04'),
 ('puja','Incense sticks','અગરબત્તી',60,'1 pack','૧ પેકેટ','photo-1608571423902-eed4a5ad8108'),
]
LEGACY_ADDITIONS = [row for row in SEED if row[1] in
                    {'Kabuli chickpeas','Whole moong','Bath soap','Shampoo','Toothpaste'}]


def connect():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL), True
    con = sqlite3.connect(os.environ.get('SQLITE_PATH', 'grocery.db'), timeout=10)
    return con, False


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
        return result
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    con, pg = connect()
    try:
        cur = con.cursor()
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
        else:
            cur.execute('PRAGMA table_info(products)')
            columns = {row[1] for row in cur.fetchall()}
            if 'image_data' not in columns:
                cur.execute('ALTER TABLE products ADD COLUMN image_data BLOB')
            if 'image_mime' not in columns:
                cur.execute('ALTER TABLE products ADD COLUMN image_mime TEXT')
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
                             f'https://images.unsplash.com/{photo}?w=600&auto=format&fit=crop&q=80'))
            marker = "INSERT INTO settings(key,value) VALUES('catalog_seed_v2','1') ON CONFLICT(key) DO UPDATE SET value=excluded.value"
            cur.execute(marker)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def settings():
    values = {'shop_name': os.environ.get('SHOP_NAME', 'Ved Grocery Mart'),
              'phone': os.environ.get('STORE_PHONE', '9979215875'),
              'whatsapp': os.environ.get('WHATSAPP_PHONE', '919979215875')}
    for row in execute('SELECT key,value FROM settings', fetch=True):
        if row['key'] in values:
            values[row['key']] = row['value']
    values['phone_link'] = re.sub(r'[^+\d]', '', values['phone'])
    values['wa_digits'] = re.sub(r'\D', '', values['whatsapp'])
    return values


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']


app.jinja_env.globals['csrf_token'] = csrf_token


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
    if data.startswith(b'\xff\xd8\xff'):
        return data, 'image/jpeg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return data, 'image/png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return data, 'image/webp'
    raise ValueError('Upload a JPG, PNG or WebP image.')


def product_payload(row):
    return dict(id=row['id'], cat=row['cat'], name_en=row['name_en'],
                name_gu=row['name_gu'], price=float(row['price']),
                unit_en=row['unit_en'], unit_gu=row['unit_gu'],
                in_stock=bool(row['in_stock']),
                image_url=url_for('product_image', item_id=row['id'])
                if row.get('has_image') else row['image_url'],
                has_upload=bool(row.get('has_image')),
                fallback_url=url_for('product_fallback',item_id=row['id']))


def all_products():
    rows = execute('''SELECT id,cat,name_en,name_gu,price,unit_en,unit_gu,
                      in_stock,image_url,(image_data IS NOT NULL) AS has_image
                      FROM products ORDER BY id''', fetch=True)
    return [product_payload(row) for row in rows]


@app.context_processor
def context():
    return {'shop': settings(), 'categories': CATEGORIES,
            'is_admin': bool(session.get('admin'))}


@app.get('/')
def home():
    lang = request.args.get('lang', 'gu')
    lang = lang if lang in ('gu','en') else 'gu'
    category = request.args.get('cat', 'all')
    category = category if category in CATEGORY_IDS else 'all'
    query = request.args.get('q', '').strip()[:80]
    all_items = all_products()
    visible = [p for p in all_items if (category == 'all' or p['cat'] == category)
               and (not query or query.casefold() in p['name_en'].casefold()
                    or query.casefold() in p['name_gu'].casefold())]
    return render_template('catalog.html', products=visible, all_items=all_items,
                           category=category, query=query, lang=lang,
                           category_labels={id:(gu,en) for id,en,gu,_ in CATEGORIES})


@app.get('/api/products')
def public_products():
    return jsonify(all_products())


@app.get('/image/<int:item_id>')
def product_image(item_id):
    row = execute('SELECT image_data,image_mime FROM products WHERE id=%s', (item_id,), one=True)
    if not row or not row['image_data']:
        abort(404)
    data = bytes(row['image_data'])
    response = send_file(io.BytesIO(data), mimetype=row['image_mime'] or 'application/octet-stream')
    response.headers['Cache-Control'] = 'public, max-age=300'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.get('/placeholder/<int:item_id>.svg')
def product_fallback(item_id):
    row = execute('SELECT name_en,cat FROM products WHERE id=%s', (item_id,), one=True)
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
    return render_template('admin.html', products=all_products())


def form_product():
    cat = request.form.get('cat', '')
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
    return (cat,name_en,name_gu,round(amount,2),unit_en,unit_gu,
            request.form.get('in_stock') == 'on',image_url,photo)


@app.post('/admin/add')
@admin_required
def add_product():
    try:
        cat,en,gu,price,unit_en,unit_gu,stock,image,photo = form_product()
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin'))
    binary,mime = photo if photo else (None,None)
    execute('''INSERT INTO products (cat,name_en,name_gu,price,unit_en,unit_gu,
               in_stock,image_url,image_data,image_mime)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (cat,en,gu,price,unit_en,unit_gu,stock,image,binary,mime),write=True)
    flash('Item added. Customers can see it now.', 'success')
    return redirect(url_for('admin'))


@app.post('/admin/item/<int:item_id>')
@admin_required
def update_product(item_id):
    if not execute('SELECT id FROM products WHERE id=%s',(item_id,),one=True):
        abort(404)
    try:
        cat,en,gu,price,unit_en,unit_gu,stock,image,photo = form_product()
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin'))
    if photo:
        execute('''UPDATE products SET cat=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url=%s,
                    image_data=%s,image_mime=%s WHERE id=%s''',
                (cat,en,gu,price,unit_en,unit_gu,stock,image,*photo,item_id),write=True)
    elif image:
        execute('''UPDATE products SET cat=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url=%s,
                    image_data=NULL,image_mime=NULL WHERE id=%s''',
                (cat,en,gu,price,unit_en,unit_gu,stock,image,item_id),write=True)
    else:
        execute('''UPDATE products SET cat=%s,name_en=%s,name_gu=%s,price=%s,
                    unit_en=%s,unit_gu=%s,in_stock=%s,image_url=%s WHERE id=%s''',
                (cat,en,gu,price,unit_en,unit_gu,stock,image,item_id),write=True)
    flash('Item updated. The public catalog now shows the new details.', 'success')
    return redirect(url_for('admin') + f'#item-{item_id}')


@app.post('/admin/delete/<int:item_id>')
@admin_required
def delete_product(item_id):
    execute('DELETE FROM products WHERE id=%s',(item_id,),write=True)
    flash('Item deleted.', 'success')
    return redirect(url_for('admin'))


@app.post('/admin/settings')
@admin_required
def update_settings():
    name = request.form.get('shop_name','').strip()[:80]
    phone = request.form.get('phone','').strip()[:22]
    whatsapp = re.sub(r'\D','',request.form.get('whatsapp',''))
    if not name or not 8 <= len(re.sub(r'\D','',phone)) <= 15 or not 8 <= len(whatsapp) <= 15:
        flash('Enter a shop name and valid call and WhatsApp numbers.', 'error')
        return redirect(url_for('admin'))
    con, pg = connect()
    try:
        cur = con.cursor()
        sql = '''INSERT INTO settings (key,value) VALUES (%s,%s)
                 ON CONFLICT(key) DO UPDATE SET value=excluded.value'''
        for key,value in [('shop_name',name),('phone',phone),('whatsapp',whatsapp)]:
            cur.execute(sql if pg else sql.replace('%s','?'), (key,value))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    flash('Shop details saved.', 'success')
    return redirect(url_for('admin'))


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
