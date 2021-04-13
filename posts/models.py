from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, null=False)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):

    class Meta:
        ordering = ["-pub_date"]

    text = models.TextField(verbose_name="Текст",
                            help_text="Введите текст поста")
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name="posts",
                              blank=True, null=True, verbose_name="Группа",
                              help_text="Выберите группу")
    image = models.ImageField(upload_to="posts/", blank=True, null=True,
                              verbose_name="Картинка")

    def __str__(self):
        return self.text


class Comment(models.Model):

    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(verbose_name="Текст",
                            help_text="Напишите текст комментария")
    created = models.DateTimeField(verbose_name="Дата публикации",
                                   auto_now_add=True)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follow")
        ]
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name="Подписчик", related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name="Подписант",
                               related_name="following")
