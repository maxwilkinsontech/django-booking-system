from django.shortcuts import redirect


class ManagerAccessMixin(object):
    redirect_url = None

    def get(self, request, *args, **kwargs):
        if not request.user.is_manager:
            return redirect(self.redirect_url)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_manager:
            return redirect(self.redirect_url)
        return super().post(request, *args, **kwargs)
