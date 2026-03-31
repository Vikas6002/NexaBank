from django.shortcuts import redirect


class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.session.get('ip'):
                request.session['ip'] = request.META.get('REMOTE_ADDR')

            if request.session['ip'] != request.META.get('REMOTE_ADDR'):
                return redirect('accounts:logout')

        return self.get_response(request)