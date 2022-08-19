from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, Comment, Follow
from .utils import paginator

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    """
    Вью функция отвечающая за вывод постов на главной странице,
    пагинируется, сортируется от новых к старым, 10 постов на страницу.
    """
    post_list = Post.objects.select_related()
    page_number = request.GET.get('page')
    page_obj = paginator(post_list).get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """
    Вью функция отвечающая за вывод постов на странице группы,
    пагинируется, сортируется от новых к старым и по принадлежности
    к группе, 10 постов на страницу.
    """
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.select_related()
    page_number = request.GET.get('page')
    page_obj = paginator(posts).get_page(page_number)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """
    Вью функция отвечающая за вывод постов на странице пользователя,
    пагинируется, сортируется от новых к старым и по принадлежности
    к пользователю, 10 постов на страницу.
    Переменная following отвечает за значение кнопки подписки/отписки
    от автора.
    """
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and author.following.exists()

    posts = author.posts.all()
    page_number = request.GET.get('page')
    page_obj = paginator(posts).get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Вью функция отвечающая за вывод одного поста
    на страницу детального прсомотра, по id
    """
    post = get_object_or_404(Post, id=post_id)
    comment = Comment.objects.filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comment,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request):
    """
    Вью функция для создания нового поста.
    """

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required()
def post_edit(request, post_id):
    """
    Вью функция для редактирования поста.
    """
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {'form': form,
                                                      'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    page_obj = paginator(post_list).get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    obj = Follow.objects.filter(user=request.user, author=author)
    obj.delete()

    return redirect('posts:follow_index')
