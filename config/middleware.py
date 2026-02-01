from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import JsonResponse
from apps.core.models import Tenant
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
   
    CACHE_TIMEOUT = 300  
    LOCALHOST_DOMAINS = ['localhost', '127.0.0.1', 'testserver']
    _redis_available = None  # Cache Redis availability check
    
    def _check_redis_available(self):
        """Check if Redis is available (cached result)"""
        if self._redis_available is None:
            try:
                cache.set('_redis_test', 1, 1)
                cache.get('_redis_test')
                TenantMiddleware._redis_available = True
            except Exception as e:
                logger.warning(f"Redis not available, caching disabled: {str(e)}")
                TenantMiddleware._redis_available = False
        return self._redis_available
    
    def _safe_cache_get(self, key):
        """Safely get from cache with fallback"""
        if not self._check_redis_available():
            return None
        try:
            return cache.get(key)
        except Exception:
            return None
    
    def _safe_cache_set(self, key, value, timeout):
        """Safely set to cache with fallback"""
        if not self._check_redis_available():
            return
        try:
            cache.set(key, value, timeout)
        except Exception:
            pass
    
    def _safe_cache_delete(self, key):
        """Safely delete from cache with fallback"""
        if not self._check_redis_available():
            return
        try:
            cache.delete(key)
        except Exception:
            pass
    
    def process_request(self, request):
       
        host = request.get_host().split(':')[0].lower()
        
        if host in self.LOCALHOST_DOMAINS:
            tenant = self._get_development_tenant()
            if tenant:
                request.tenant = tenant
                request.tenant_domain = host
                return None
            else:
                logger.warning("No development tenant configured. Create a tenant with domain 'localhost'")
                return JsonResponse({
                    'error': 'Development tenant not configured',
                    'detail': 'Please create a tenant with domain "localhost" for local development'
                }, status=500)
        
        cache_key = f'tenant_domain_{host}'
        tenant_id = self._safe_cache_get(cache_key)
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                request.tenant = tenant
                request.tenant_domain = host
                return None
            except Tenant.DoesNotExist:
                self._safe_cache_delete(cache_key)
        
        tenant = self._get_tenant_by_domain(host)
        
        if tenant:
            self._safe_cache_set(cache_key, tenant.id, self.CACHE_TIMEOUT)
            request.tenant = tenant
            request.tenant_domain = host
            return None
        
        logger.warning(f"No tenant found for domain: {host}")
        return JsonResponse({
            'error': 'Invalid domain',
            'detail': f'No tenant registered for domain: {host}'
        }, status=404)
    
    def _get_tenant_by_domain(self, host):
      
        try:
            tenant = Tenant.objects.filter(
                domain=host,
                is_active=True
            ).first()
            
            if tenant:
                return tenant
            
            tenants = Tenant.objects.filter(is_active=True)
            for tenant in tenants:
                if host in tenant.get_all_domains():
                    return tenant
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving tenant for domain {host}: {str(e)}")
            return None
    
    def _get_development_tenant(self):
     
        try:
            tenant = Tenant.objects.filter(
                domain='localhost',
                is_active=True
            ).first()
            
            if tenant:
                return tenant
            
            return Tenant.objects.filter(is_active=True).first()
        except Exception as e:
            logger.error(f"Error retrieving development tenant: {str(e)}")
            return None
    
    def process_response(self, request, response):
      
        if hasattr(request, 'tenant') and request.tenant:
            response['X-Tenant-ID'] = str(request.tenant.id)
            response['X-Tenant-Name'] = request.tenant.name
        
        return response
