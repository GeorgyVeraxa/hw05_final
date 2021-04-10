from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings

from .forms import CommentForm, PostForm
from .models import Group, Post, Follow, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get("page")
    # Получаем набор записей для страницы с запрошенным номером
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {"page": page, }
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get("page")
    # Получаем набор записей для страницы с запрошенным номером
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {"page": page, "group": group, }
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new.html", {"form": form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    current_user = request.user
    post_list = user.posts.all()
    post_list_count = post_list.count()

    following = False
    if current_user.is_authenticated and current_user != user:
        following = current_user.follower.filter(author=user).exists()

    paginator = Paginator(post_list, 10)

    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get("page")

    # Получаем набор записей для страницы с запрошенным номером
    page = paginator.get_page(page_number)
    return render(request, "profile.html",
                  {"page": page,
                   "author": user,
                   "count": post_list_count,
                   "current_user": current_user,
                   "following": following,
                   })


def post_view(request, username, post_id):

    current_user = request.user
    post = get_object_or_404(Post, id=post_id, author__username=username)
    user = post.author
    users_post_count = user.posts.all().count()
    form = CommentForm()
    comments = post.comments.all()
    return render(request, "post.html",
                  {"author": user,
                   "post": post,
                   "count": users_post_count,
                   "current_user": current_user,
                   "form": form,
                   "comments": comments,
                   })


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=username, post_id=post_id)
    # добавим в form свойство files
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username,
                            post_id=post_id)
    return render(request, "new.html",
                  {"form": form,
                   "post": post
                   })


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("post", username, post_id)


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, settings.POST_PER_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    form = CommentForm()
    return render(request, "follow.html",
                  {"page": page,
                   "paginator": paginator,
                   "form": form,
                   })


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if author != user:
        Follow.objects.get_or_create(author=author, user=user)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):

    user = request.user
    author = get_object_or_404(User, username=username)
    if author.following.filter(user=user).exists() and author != user:
        Follow.objects.filter(author=author, user=user).delete()
    return redirect("profile", username=username)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, "misc/404.html",
                  {"path": request.path},
                  status=404
                  )


def server_error(request):
    return render(request, "misc/500.html", status=500)
