from django.forms.models import ModelForm
from django.forms import Textarea
from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["group", "text", "image"]


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {"text": Textarea(attrs={"cols": 80, "rows": 1})}
