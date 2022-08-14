from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:

        model = Post

        fields = ('group', 'text', 'image')
        help_texts = {'text': 'Текст нового поста',
                      'group': 'Группа, к которой будет относиться пост', }
        labels = {'text': 'Текст поста',
                  'group': 'Группа', }


class CommentForm(forms.ModelForm):
    class Meta:

        model = Comment

        fields = ('text',)
        help_texts = {'text': 'Текст нового комментария', }
        labels = {'text': 'Текст комментария', }
