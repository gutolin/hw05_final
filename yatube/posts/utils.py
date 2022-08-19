from django.conf import settings
from django.core.paginator import Paginator


def paginator(data):
    return Paginator(data, settings.POSTS_AMOUNT_ON_PAGE)
