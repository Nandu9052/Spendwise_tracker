from django.conf import settings
from django.urls import set_script_prefix
from django.shortcuts import redirect


class DynamicCsrfMiddleware:
    """
    1. Dynamically trusts incoming Origin and Host headers so CSRF works
       under any proxy (LEARNSQUARE, SemesterPrep, Codespaces, etc.)
    2. Normalizes any double-proxy paths like /proxy/8000/proxy/8000/...
       so routes resolve cleanly.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── 1. Clean up duplicate proxy prefixes ──────────────────────────
        # Code-server already rewrites redirects to /proxy/8000/.
        # If double-prefixed paths arrive, strip them to normal paths.
        while request.path_info.startswith('/proxy/8000'):
            request.path_info = request.path_info[len('/proxy/8000'):] or '/'
        while request.path_info.startswith('/absproxy/8000'):
            request.path_info = request.path_info[len('/absproxy/8000'):] or '/'

        # Always keep script prefix default so code-server's reverse proxy
        # handles external rewriting without double-prefix collisions.
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
