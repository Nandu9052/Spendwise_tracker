from django.conf import settings


class DynamicCsrfMiddleware:
    """
    Dynamically trusts the incoming Origin and Host headers so that POST
    forms work seamlessly in ANY environment:

      - localhost / 127.0.0.1 direct access
      - Docker / Coder container port-forwarding
      - Gitpod / GitHub Codespaces
      - LEARNSQUARE / SemesterPrep reverse-proxy  ← this is the key use case
      - Any other HTTPS tunnel (ngrok, cloudflared, VS Code port forward …)

    How it works
    ────────────
    LEARNSQUARE exposes your Django app through an HTTPS reverse proxy whose
    hostname looks like:

        https://team-284-global.dev.semesterprep.in:8443/proxy/8000/

    The browser sends  Origin: https://team-284-global.dev.semesterprep.in:8443
    on every POST request. Django 4+ rejects POST requests whose Origin is not
    in CSRF_TRUSTED_ORIGINS.

    This middleware reads the Origin (and Host) of EVERY incoming request
    BEFORE Django's CsrfViewMiddleware runs, and adds the origin to the
    trusted list on the fly — so CSRF verification always passes without
    hard-coding any domain.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── 1. Trust the HTTP Origin header ───────────────────────────────
        origin = request.META.get('HTTP_ORIGIN', '').strip()
        if origin and origin not in settings.CSRF_TRUSTED_ORIGINS:
            settings.CSRF_TRUSTED_ORIGINS.append(origin)

        # ── 2. Trust the Host (covers non-browser clients that omit Origin) ─
        try:
            host = request.get_host()   # returns  host  or  host:port
            if host:
                for scheme in ('http://', 'https://'):
                    candidate = f'{scheme}{host}'
                    if candidate not in settings.CSRF_TRUSTED_ORIGINS:
                        settings.CSRF_TRUSTED_ORIGINS.append(candidate)
        except Exception:
            pass

        # ── 3. Trust X-Forwarded-Host if the proxy sets it ────────────────
        fwd_host = request.META.get('HTTP_X_FORWARDED_HOST', '').strip()
        if fwd_host:
            for scheme in ('http://', 'https://'):
                candidate = f'{scheme}{fwd_host}'
                if candidate not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(candidate)

        return self.get_response(request)
