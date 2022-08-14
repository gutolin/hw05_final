from django.core.paginator import Paginator
from django.conf import settings


def paginator(data):
    return Paginator(data, settings.POSTS_AMOUNT_ON_PAGE)
