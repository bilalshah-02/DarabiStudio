# Darabi Studio — Online Store

## Run locally
1. `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
2. `pip install -r requirements.txt`
3. `python manage.py migrate`
4. `python manage.py createsuperuser`
5. `python manage.py runserver`
6. Visit http://127.0.0.1:8000/  |  Admin: http://127.0.0.1:8000/admin/

## Add products
Go to /admin/ → Products → Add. Upload photos, set price/stock, mark "is_featured" for homepage.

## Demo login (this sandbox copy only — change before real use)
admin / darabi123

## Payment methods
Cash on Delivery and Bank Transfer work out of the box (manual confirmation).
JazzCash, Easypaisa, and Card need merchant accounts + API keys before they can auto-charge —
see next steps.

## Production checklist before going live
1. Copy `.env.example` to `.env` and fill in real values (SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL, email, etc.)
2. Set `DEBUG=False` in `.env`
3. Fill in the [DATE], [X days], [YOUR EMAIL] etc. placeholders in the 4 legal pages
   (store/templates/store/legal/) with your actual policy details
4. Get JazzCash / Easypaisa / card merchant approval (needs the legal pages + HTTPS live)
5. Run `python manage.py collectstatic` before deploying
6. Point CLOUDINARY_URL at a free Cloudinary account so product photos survive redeploys
