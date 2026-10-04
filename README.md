# Ved Grocery Mart — Flask / Railway

A Gujarati and English mobile storefront in a dark dashboard theme using **JetBrains Mono** with Noto Sans Gujarati glyphs. Customers browse without logging in, filter by category, brand, price, stock or offers, choose a brand and pack size, and save a shopping list on their device. They can submit a numbered order request for shop pickup or configured local delivery; the shopkeeper sees it on the protected order board and can update its status. Customers can also call using `tel:` or send the list through WhatsApp using `wa.me`. **WhatsApp requires the customer to tap Send; numbered requests do not take payment.** The shopkeeper alone signs in to edit products, variants, photos, prices, stock, offers, contact numbers, fulfillment settings and order status.

## Files

- `app.py`: Flask routes, admin security and SQLite/PostgreSQL support.
- `catalog_data.py`: ten bilingual categories, subcategories and unpublished product suggestions.
- `templates/`: storefront and admin screens.
- `static/`: responsive dark UI, cart JavaScript, compressed WebP hero image and image fallback.
- `static/manifest.webmanifest`, `service-worker.js`, `offline.html` and icons: installable mobile PWA.
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

The app uses PostgreSQL on Railway; SQLite is for local development only. Photo uploads (JPG, PNG or WebP, up to 3 MB) are resized to a maximum of 720×720 and saved as WebP database bytes, so they survive app restarts and redeployments. Existing uploaded photos remain unchanged. Set Railway database backups and review image storage as the catalog grows. The browser cart saves variant IDs and quantities on that device; checkout recalculates prices and stock from the database. Cart data does not sync between phones. Orders are stored in PostgreSQL and remain visible on the admin order board across redeployments. An order request is pending until the shopkeeper confirms it; there is no online payment or automatic WhatsApp notification.

## Install on a phone

Open the Railway HTTPS website in Chrome on Android and choose **Install app** or **Add to Home screen** from the browser menu; on iPhone, open it in Safari and use **Share → Add to Home Screen**. The installed site opens like an app. It needs a live connection to show current products, prices, submit requests and contact WhatsApp. If offline, it shows a reconnect screen instead of stale prices. The shopping list stays on the same device/browser storage, including when the PWA is installed from that browser where supported. The app name in the manifest is Ved Grocery Mart; customize the name and icons for each new shop.

## Speed and capacity

This release combines the product and pack-size catalog reads into one database query. Once the schema migration has completed, later worker starts skip the DDL and demo-photo checks. Uploaded image URLs change when the owner replaces an image, allowing the browser to keep unchanged photos for a week. The `/healthz` endpoint checks that the web worker responds without involving PostgreSQL; compare it with `/` to isolate database/catalog delay. Demo photos still come from Unsplash and their external loading speed can vary. Uploading the merchant's real compressed pictures removes that third-party dependency.

On Railway, first compare the web service and PostgreSQL service regions. Put them in the same region. If most customers are in Gujarat, Singapore is a reasonable nearby choice, but moving PostgreSQL's volume requires a backup and may cause downtime; moving the web service to the existing database region is a simpler diagnostic. Use the database service's private `DATABASE_URL` reference, not its public TCP proxy address. If Railway **Serverless** is enabled on the web service, a first request after idle can be slow; switch it off if consistently quick first visits matter more than idle savings. Check Railway's HTTP logs and CPU/memory metrics before raising replica counts. This ZIP does not change Railway settings or the live deployment.

The shop settings and product list are cached in each app worker for up to 30 seconds. Admin writes invalidate that worker's cache immediately; with multiple workers or replicas, other workers can display old values for up to 30 seconds. Postgres connections are pooled per worker (up to eight). The initial HTML includes product data, so the browser only refreshes the product API when the customer opens the saved shopping list. The hero is a 147 KB WebP instead of a 2.6 MB PNG; demo thumbnails request smaller files. Uploaded photos are compressed for future items.

For best latency, put the web app and PostgreSQL in the same Railway region. Changing the region of a database with an attached volume migrates the volume and causes temporary downtime; make a backup and schedule the move. Keep the app in an India-near region, such as Singapore, if most customers are in Gujarat. Two Gunicorn workers with four threads each handle up to eight concurrent requests per service instance; actual visitor capacity depends on the Railway plan, photo size and traffic. Monitor CPU, memory and HTTP latency before adding replicas.

## Daily shopkeeper updates

The customer catalog now has ten top-level categories. Their subcategories appear when the shop has published products in them. The owner sees 397 Gujarati and English suggestions under **Choose products your shop sells**. Suggestions are not customer listings and have no guessed price or picture. Selecting one fills the new-product form; the owner supplies the real price, pack size and actual photo before saving. Existing store products, prices, orders and photos are retained when the old category identifiers are mapped to the new taxonomy. The owner can hide a product from customers without deleting old requests, and publish it again later. The **Daily price desk** lets the owner search products and change each pack's price and availability in a short row. Search supports both names, category words and optional aliases; add spellings such as `tuver toor arhar` to the alias field for each item. Seasonal goods are suggestions under Household and can be published only while stocked. For fresh produce the site tells customers that actual weight and final price require shopkeeper confirmation. Customers can ask the shop to call before replacing an unavailable item or to avoid substitutions; the preference appears in the order note. No automatic weight adjustment, payments, or stock quantity ledger is included.

Sign in at /login. The inventory is grouped by category. Click **Add here** beside a category to preselect it in the new item form, then enter the Gujarati and English names, price, units and a required photo upload or HTTPS link. Open an existing item's editor to upload/replace its photo, change its category, edit its original pack or add more brands and pack sizes with individual prices, stock and optional crossed-out comparison prices. Remove added packs or delete a product as needed. The original pack can be edited but not removed separately. Under shop settings, enable pickup and/or delivery, set the pickup address, hours, delivery pincodes and fee, and minimum order. Delivery starts disabled until the shopkeeper enters serviceable six-digit pincodes. The **Orders** board shows the latest 100 requests and lets the shopkeeper change their status. Only the shopkeeper can access these actions. Changes are saved to PostgreSQL and show to customers after refresh (other workers may serve cached catalog data for up to 30 seconds); no code deployment is needed for daily edits. The initial items and photos are examples. Replace every example price and photograph before public use.

If Railway blocks creating a new project under the current plan, the service cannot be made live there until the account's project limit changes. This code package does not alter the existing Railway projects.

## Existing database

The app retains the original `products` table and adds `image_data`, `image_mime`, bilingual subcategory, aliases and publication status columns when missing. It keeps existing products and prices. On startup it creates `product_variants` and one original pack for every existing product, plus an `orders` table. A one-time migration maps old categories to the new ten-category structure. This migration is automatic; back up the Railway database before the first deployment. A fresh database receives demo products; an existing catalog receives five missing example pulse/bath products once, without replacing existing items. Existing browser shopping lists are migrated to the original pack where possible. The previous `admin/admin` password does not work in this version; the hash must be set in the environment.
