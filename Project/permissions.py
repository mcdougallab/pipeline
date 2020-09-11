"""permissions rules"""


def statistics(request):
    return request.user.is_authenticated
