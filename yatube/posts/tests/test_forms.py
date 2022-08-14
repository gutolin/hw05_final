import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
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
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            image=cls.uploaded
        )

        cls.form = PostsCreateFormTests()

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.tasks_count = Post.objects.count()

    def test_create_posts(self):
        """Валидная форма создает запись в Post."""

        form_data = {
            'text': 'test Text',
            'group': self.group.id,
            'image': self.uploaded
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), self.tasks_count + 1)

        last_post = Post.objects.first()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group, self.group)
        self.assertEqual(last_post.author, self.author)
        self.assertEqual(last_post.image, form_data['image'])

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""

        group2 = Group.objects.create(
            title='Группа для редактирования',
            slug='group_edit_slug',
            description='Тестовое описание',
        )
        form_data = {
            'text': 'edit text',
            'group': group2.id,
            'image': self.uploaded
        }
        self.author_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data, follow=True
        )

        self.assertEqual(Post.objects.count(), self.tasks_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=group2,
                image=form_data['image']
            ).exists()
        )

    def test_guest_create_post(self):
        self.guest_client = Client()

        form_data = {'text': 'test Text', 'group': self.group.id}
        response = self.guest_client.post(
            reverse('posts:post_create',),
            data=form_data, follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

        self.assertEqual(Post.objects.count(), self.tasks_count)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='user')
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.comment_count = Comment.objects.count()

    def test_comment_create(self):
        """Валидная форма создает комментарии"""

        form_data = {
            'text': 'test Text',
        }
        self.user_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.filter(post_id=self.post.id).count(),
                         self.comment_count + 1)

        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                post=self.post.id
            ).exists()
        )

    def test_guest_create_comment(self):
        """Неавторизированный пользователь не может оставить комментарий"""
        self.guest_client = Client()

        form_data = {'text': 'test Text'}
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.filter(post_id=self.post.id).count(),
                         self.comment_count)
