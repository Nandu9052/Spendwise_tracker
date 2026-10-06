from django.conf import settings
from django.urls import set_script_prefix


class DynamicCsrfMiddleware:
    """
    1. Dynamically trusts incoming Origin and Host headers so CSRF works
       seamlessly under any proxy (LEARNSQUARE, SemesterPrep, Codespaces, etc.)
    2. Automatically detects code-server reverse proxy (/proxy/8000/) and sets
       Django's script prefix so all URLs, links ({% url ... %}), and redirects
       (redirect('dashboard')) automatically stay inside /proxy/8000/ instead of
       stripping the prefix and hitting port 8443 directly with 404 Not Found.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── 1. Detect Reverse Proxy Prefix (code-server / LEARNSQUARE) ───
        prefix = ''
        
        # Check explicit forward headers
        fwd_prefix = request.META.get('HTTP_X_FORWARDED_PREFIX', '').strip()
        if fwd_prefix:
            prefix = fwd_prefix
        elif request.path_info.startswith('/proxy/8000'):
            prefix = '/proxy/8000'
            request.path_info = request.path_info[len('/proxy/8000'):] or '/'
        elif request.path_info.startswith('/absproxy/8000'):
            prefix = '/absproxy/8000'
            request.path_info = request.path_info[len('/absproxy/8000'):] or '/'
        else:
            # Check if accessed via port 8443 (LEARNSQUARE code-server port)
            host = request.get_host()
            fwd_host = request.META.get('HTTP_X_FORWARDED_HOST', '')
            referer = request.META.get('HTTP_REFERER', '')
            if ':8443' in host or ':8443' in fwd_host or '/proxy/8000' in referer:
                prefix = '/proxy/8000'

        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            set_script_prefix(prefix)
        else:
            set_script_prefix('/')

        # ── 2. Trust HTTP Origin & Host for CSRF ─────────────────────────
        origin = request.META.get('HTTP_ORIGIN', '').strip()
        if origin and origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(origin)

        try:
            host = request.get_host()
            if host:
                for scheme in ('http://', 'https://'):
                    candidate = f'{scheme}{host}'
                    if candidate not in settings.CSRF_TRUSTED_ORIGINS:
                        settings.CSRF_TRUSTED_ORIGINS.append(candidate)
        except Exception:
            pass

        fwd_host = request.META.get('HTTP_X_FORWARDED_HOST', '').strip()
        if fwd_host:
            for scheme in ('http://', 'https://'):
                candidate = f'{scheme}{fwd_host}'
                if candidate not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(candidate)

        response = self.get_response(request)
        return response
