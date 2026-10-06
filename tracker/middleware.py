from django.conf import settings

class DynamicCsrfMiddleware:
    """
    Dynamically trusts the incoming Origin and Host so that POST forms work
    seamlessly in any environment (localhost, Docker/Coder container,
    VS Code port-forwarding, Gitpod, Codespaces, or hackathon proxy).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.META.get('HTTP_ORIGIN')
        if origin and origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(origin)
        
        try:
            host = request.get_host()
            if host:
                for scheme in ('http://', 'https://'):
                    candidate = f"{scheme}{host}"
                    if candidate not in settings.CSRF_TRUSTED_ORIGINS:
                        settings.CSRF_TRUSTED_ORIGINS.append(candidate)
        except Exception:
            pass

        return self.get_response(request)
