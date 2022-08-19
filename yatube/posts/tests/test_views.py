import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            image=cls.uploaded
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:posts_index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'author'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})
            ),
            'posts/create_post.html': (
                reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})
            ),

        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def post_context_check(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:posts_index'))
        post = response.context['page_obj'][0]
        self.post_context_check(post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug'})
        ))
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        ))
        post = response.context['page_obj'][0]
        self.post_context_check(post)
        self.assertEqual(self.author, self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        ))
        post = response.context['post']
        self.post_context_check(post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        ))
        self.assertIsInstance(response.context.get('form'), PostForm)

        self.assertIsInstance(response.context.get('is_edit'), bool)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_wrong_group(self):
        Group.objects.create(
            title='Тестовая группа2',
            slug='slug2',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=self.author,
            text='Тестовый пост',
        )

        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'slug2'})
        ))
        group = response.context['group']
        self.assertNotEqual(group.title, self.group.title)

    def test_404_page(self):
        """Ошибка 404 вызывает кастомный шаблон"""
        response = self.authorized_client.get('/sdgfsadfg')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_post_context_check(self):
        """Главная страница получает данные из кэша"""
        response = self.authorized_client.get(reverse('posts:posts_index'))
        response_cache = self.authorized_client.get(
            reverse('posts:posts_index')
        )
        self.assertTrue(response.context)
        self.assertFalse(response_cache.context)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PostsPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')

        posts_count_for_test = 12
        cls.posts_on_second_page = (
            posts_count_for_test - settings.POSTS_AMOUNT_ON_PAGE)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = [
            Post(author=cls.author, text='Тестовый пост', group=cls.group)
            for x in range(posts_count_for_test)
        ]
        Post.objects.bulk_create(cls.post)

        Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

        cls.pages_url = {
            'index': '/',
            'group_list': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.author}/',
            'follow': '/follow/'
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        for pages in self.pages_url.values():
            with self.subTest(pages=pages):
                response = self.authorized_client.get(pages)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_AMOUNT_ON_PAGE
                )

    def test_second_page_contains_three_records(self):
        for pages in self.pages_url.values():
            with self.subTest(pages=pages):
                response = self.authorized_client.get(pages + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.posts_on_second_page
                )


class PostsFollowingTests(TestCase):
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
            text='Тестовый пост'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='user')
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.user_following_author()

    def user_following_author(self):
        self.user_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )

    def test_post_following(self):
        """Авторизированный пользователь может подписаться на автора"""

        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_post_following(self):
        """Авторизированный пользователь может отписаться от автора"""
        self.user_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )

        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def post_context_check(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)

    def test_index_page_show_correct_context(self):
        """Шаблон follow сформирован с правильным контекстом."""

        response = self.user_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]

        self.post_context_check(post)

        self.user_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author})
        )
        response = self.user_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj']
        for data in post:
            self.assertEqual(data, None)

    def test_new_posts_from_followng_author(self):
        """Новый пост от отслеживаемого автора появляется
        на странице подписок."""
        response = self.user_client.get(reverse('posts:follow_index'))
        post_count = len(response.context['page_obj'])

        Post.objects.create(
            author=self.author,
            text='text'
        )

        response = self.user_client.get(reverse('posts:follow_index'))
        second_post_count = len(response.context['page_obj'])

        self.assertEqual(second_post_count, post_count + 1)

    def test_new_posts_from_user(self):
        """Новый пост от неотслеживаемого автора непоявляется
        на странице подписок."""
        response = self.user_client.get(reverse('posts:follow_index'))
        post_count = len(response.context['page_obj'])

        random_user = User.objects.create_user(username='random_user')
        Post.objects.create(
            author=random_user,
            text='text'
        )

        response = self.user_client.get(reverse('posts:follow_index'))
        second_post_count = len(response.context['page_obj'])

        self.assertEqual(second_post_count, post_count)
