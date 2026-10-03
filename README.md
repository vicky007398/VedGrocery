# Ved Grocery Mart — Flask / Railway

A Gujarati and English mobile storefront in a dark dashboard theme using **JetBrains Mono** with Noto Sans Gujarati glyphs. Customers browse without logging in, save a shopping list on their own device, call the shop using `tel:`, or send the current list to WhatsApp using `wa.me`. **Opening WhatsApp does not place an order automatically**; the customer must tap Send there. The shopkeeper alone signs in to edit products, photos, prices, stock and contact numbers.

## Files

- `app.py`: Flask routes, admin security and SQLite/PostgreSQL support.
- `templates/`: storefront and admin screens.
- `static/`: responsive dark UI, cart JavaScript, compressed WebP hero image and image fallback.
- `requirements.txt` and `Procfile`: Railway build and start instructions.

## Local run

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/hash_password.py
```

The password generator accepts 5 or more characters, prompts without echoing the password and prints a hash. A longer unique password is safer when the admin page is public. Set `ADMIN_PASSWORD_HASH` to that hash, `ADMIN_USERNAME` to the shopkeeper's username and `SECRET_KEY` to a random string (`python -c "import secrets; print(secrets.token_hex(32))"`). Set the optional `SHOP_NAME`, `STORE_PHONE` and `WHATSAPP_PHONE` as shown in `.env.example`. Export variables in your shell or load them from a private `.env` file with your own environment loader. The app itself does not automatically read `.env`. Run `python app.py`, then open `http://localhost:5000`. Local SQLite uses `grocery.db`.

## Railway deployment

1. Create a new Railway project and connect this folder's GitHub repository. Add a Railway **PostgreSQL** service in that project. Railway exposes `DATABASE_URL` to the database service; add a `DATABASE_URL` variable to the web service referencing the database service's connection string (for example `${{Postgres.DATABASE_URL}}`, with your service's actual name).
2. Set `SECRET_KEY`, `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` on the web service. `SECRET_KEY` must stay the same across deployments. Optionally set `STORE_PHONE`, `WHATSAPP_PHONE` (country code + number, digits only) and `SHOP_NAME`. After deployment, the shopkeeper can change the contact numbers and name at `/admin`.
3. Railway should detect `requirements.txt` and the `Procfile`. If it asks for a start command, use `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60 --keep-alive 5 app:app`.
4. In the web service's Networking settings, select **Generate Domain**. The customer URL is the domain root; the admin login is `/login` or `/admin`. The initial catalog uses example items and prices. **Replace every example price and photograph before sharing the domain with customers.**

The app uses PostgreSQL on Railway; SQLite is for local development only. Photo uploads (JPG, PNG or WebP, up to 3 MB) are resized to a maximum of 720×720 and saved as WebP database bytes, so they survive app restarts and redeployments. Existing uploaded photos remain unchanged. Set Railway database backups and review image storage as the catalog grows. The browser cart saves only product IDs and quantities on that device; catalog prices come from the live server. Cart data does not sync between phones.

## Speed and capacity

The shop settings and product list are cached in each app worker for up to 30 seconds. Admin writes invalidate that worker's cache immediately; with multiple workers or replicas, other workers can display old values for up to 30 seconds. Postgres connections are pooled per worker (up to eight). The initial HTML includes product data, so the browser only refreshes the product API when the customer opens the saved shopping list. The hero is a 147 KB WebP instead of a 2.6 MB PNG; demo thumbnails request smaller files. Uploaded photos are compressed for future items.

For best latency, put the web app and PostgreSQL in the same Railway region. Changing the region of a database with an attached volume migrates the volume and causes temporary downtime; make a backup and schedule the move. Keep the app in an India-near region, such as Singapore, if most customers are in Gujarat. Two Gunicorn workers with four threads each handle up to eight concurrent requests per service instance; actual visitor capacity depends on the Railway plan, photo size and traffic. Monitor CPU, memory and HTTP latency before adding replicas.

## Daily shopkeeper updates

Sign in at /login. The inventory is grouped by category. Click **Add here** beside a category to preselect it in the new item form, then enter the Gujarati and English names, price, units and a required photo upload or HTTPS link. Open an existing item's editor to upload/replace its photo, change its category and price, mark it unavailable, remove its photo or delete the item. Only the shopkeeper can access these actions. Changes are saved to PostgreSQL and show immediately to customers after refresh; no code deployment is needed for daily edits. The 19 initial items have example photo links. Two repeated example photos are corrected by this release without changing merchant uploads, custom links or prices. For dependable product packaging pictures, upload each shop owner's actual photo.

If Railway blocks creating a new project under the current plan, the service cannot be made live there until the account's project limit changes. This code package does not alter the existing Railway projects.

## Existing database

The app retains the original `products` table and adds `image_data` and `image_mime` columns when missing. It keeps existing products and prices. A fresh database receives 19 demo products; an existing catalog receives five missing example pulse/bath products once, without replacing existing items. The previous `admin/admin` password does not work in this version; the hash must be set in the environment.
