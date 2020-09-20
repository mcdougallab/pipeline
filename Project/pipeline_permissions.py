"""permissions rules"""


def statistics(request):
    return request.user.is_authenticated


def update(request):
    return request.user.is_authenticated


def browse(request):
    return request.user.is_authenticated


def review(request):
    return request.user.is_authenticated
