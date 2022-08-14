from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.pages_url = {
            'index': '/',
            'group_list': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.post.author}/',
            'post_detail': f'/posts/{cls.post.id}/',
        }
        cls.create_ulr = '/create/'
        cls.edit_ulr = f'/posts/{cls.post.id}/edit/'

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='user')
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': self.pages_url['index'],
            'posts/group_list.html': self.pages_url['group_list'],
            'posts/profile.html': self.pages_url['profile'],
            'posts/post_detail.html': self.pages_url['post_detail']
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template,)

    def test_pages_available_for_guests(self):
        """Страницы дотупны для всех польсзователей."""
        for url in self.pages_url.values():
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_access(self):
        """Страница создания поста доступна
        только авторизированным пользователям."""
        response = self.guest_client.get(self.create_ulr)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        response = self.user_client.get(self.create_ulr)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_access(self):
        """Страница редактирования поста доступна
        только автору поста."""
        response = self.guest_client.get(self.edit_ulr)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        response = self.user_client.get(self.edit_ulr)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404_error(self):
        """Несуществующий URL-адрес возвращает http code 404."""
        response = self.guest_client.get('/uexpexted_url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
