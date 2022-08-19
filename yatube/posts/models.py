from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Group(models.Model):
    """
    Модель групп, к которым можно прикреплять посты,
    для дальнейшей сортировки по принадлежности к группе.
    Имеет:
        Название
        Ссылку на группу - будет отобраджаться в адрессной строке
        описание группы.
    """

    title = models.CharField(verbose_name='Название группы', max_length=200)
    slug = models.SlugField(verbose_name='Cсылка на группу', unique=True)
    description = models.TextField(verbose_name='Описание группы')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        if self.title is None:
            return "Пустое имя группы"
        else:
            return self.title


class Post(models.Model):
    """
    Модель постов. Основная модель сайта
    Имеет:
        Название
        Дату публикации - автоматически задается по дате сервера
        Принадлежность к автору - помечает какой пользователь создал пост
        Принадлежность к группе - опциональный параметр, отвечающий за
        привязку поста к определенной группе.
    """

    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField('post create date', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор поста',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='group_posts',
        verbose_name='Принадлежность к группе'
    )

    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):

    text = models.TextField(verbose_name='Текст')
    created = models.DateTimeField('post create date', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_author',
        verbose_name='Автор комментария',
    )
    post = models.ForeignKey(
        Post,
        blank=True,
        on_delete=models.CASCADE,
        related_name='post_comment',
        verbose_name='Принадлежность к посту'
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        UniqueConstraint(fields=['user', 'author'], name='unique_follow')

    def __str__(self):
        return f'{self.user} following {self.author}'
