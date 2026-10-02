from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from store.sitemaps import ProductSitemap, StaticViewSitemap
from store.admin_views import dashboard, customers

sitemaps = {"products": ProductSitemap, "pages": StaticViewSitemap}

urlpatterns = [
    path('admin/dashboard/', dashboard, name='store_dashboard'),
    path('admin/customers/', customers, name='store_customers'),
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name='robots'),
    path('', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'store.views.error_404'
handler500 = 'store.views.error_500'
