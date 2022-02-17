import os
import boto3
import uuid
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.template.defaultfilters import register
from .models import Group, Event, Profile, Recipe, Vote, PhotoGroup, PhotoEvent, PhotoRecipe
from .forms import EventForm, ProfileForm, RecipeForm

# Custom Filter
@register.filter
def get_item(dictionary, key):
  return dictionary.get(key)


class GroupUpdate(LoginRequiredMixin, UpdateView):
  model = Group
  fields = ['name', 'description']


class GroupDelete(LoginRequiredMixin, DeleteView):
  model = Group
  success_url = '/dashboard/'


def home(request):
  return render(request, 'home.html')

@login_required
def dashboard (request):
  profile = Profile.objects.get(user=request.user)
  groups = Group.objects.filter(members=profile)
  return render(request, 'dashboard.html', {'groups': groups})

@login_required
def groups_index(request):
  groups = Group.objects.all()
  return render(request, 'groups/index.html', {'groups': groups})

@login_required
def groups_detail(request, group_id):
  group = Group.objects.get(id=group_id)
  # events = Event.objects.get(id=group_id)
  event_form = EventForm()
  return render(request, 'groups/detail.html',{'group': group, 'event_form': event_form})

@login_required
def events_detail(request, event_id):
  event = Event.objects.get(id=event_id)

  recipes_in_event = Recipe.objects.filter(events=event_id)
  recipes_not_in_event = Recipe.objects.exclude(events=event_id, user=request.user)

  votes = Vote.objects.filter(event_id=event_id).values('recipe_id').annotate(cnt=models.Count('recipe_id'))
  tally = {}
  for r in votes:
    tally[r['recipe_id']] = r['cnt']

  return render(request, 'events/detail.html', {
    'event': event,
    'recipes_not_in_event': recipes_not_in_event,
    'recipes_in_event': recipes_in_event,
    'tally': tally,
  })

@login_required
def add_event(request, group_id):
  #create a ModelForm instance using the data in request.POST
  form = EventForm(request.POST)
  #check if form is valid
  if form.is_valid():
    # don't want to try to save the feeding
    # until the cat_id has been assigned
    new_event = form.save(commit=False)
    new_event.group_id = group_id
    new_event.save()
  return redirect('detail', group_id=group_id)

@login_required
def events_create(request, group_id):
  event_form = EventForm()
  return render(request, {'event_form': event_form}, group_id=group_id)


def signup(request):
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect ('profile_form')
    else:
      error_message = 'Invalid Sign Up, Try Again'
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)


def profile_form(request):
  profile_form = ProfileForm()
  return render(request, 'registration/profile_form.html', {'profile_form': profile_form})

@login_required
def add_profile(request):
  current_user = request.user
  #create a ModelForm instance using the data in request.POST
  form = ProfileForm(request.POST)
  #check if form is valid
  if form.is_valid():
    new_profile = form.save(commit=False)
    new_profile.user = current_user
    new_profile.save()
  return redirect('dashboard')


class GroupCreate(LoginRequiredMixin, CreateView):
  model = Group
  fields = ['name', 'description']

  # This inherited method is called when a
  # valid group form is being submitted
  def form_valid(self, form):
    # form.instance is the group object
    form.instance.user = self.request.user
    form.instance.leader = self.request.user.username
    return super().form_valid(form)

@login_required
def add_event(request, group_id):
  #create a ModelForm instance using the data in request.POST
  form = EventForm(request.POST)
  #check if form is valid
  if form.is_valid():
    # don't want to try to save the feeding
    # until the cat_id has been assigned
    new_event = form.save(commit=False)
    new_event.group_id = group_id
    new_event.save()
  return redirect('detail', group_id=group_id)

@login_required
def events_create(request, group_id):
  event_form = EventForm()
  return render(request, {'event_form': event_form}, group_id=group_id)

# # Class-Based View (CBV)


@login_required
def assoc_profile(request, group_id):
  profile_id = Profile.objects.get(user=request.user)
  group = Group.objects.get(id=group_id)
  group.members.add(profile_id)
  return redirect('detail', group_id=group_id)

@login_required
def unassoc_profile(request, group_id):
  profile_id = Profile.objects.get(user=request.user)
  group = Group.objects.get(id=group_id)
  group.members.remove(profile_id)
  return redirect('detail', group_id=group_id)

@login_required
def recipes_index(request):
  recipe_form = RecipeForm()
  recipes = Recipe.objects.filter(user=request.user)
  return render(request, 'recipes/index.html', {
    'recipe_form': recipe_form, 
    'recipes': recipes
  })

@login_required
def add_recipe(request):
  form = RecipeForm(request.POST)
  if form.is_valid():
    new_recipe = form.save(commit=False)
    new_recipe.user = request.user
    new_recipe.save()
    print('hello')
  return redirect('recipes_index')

@login_required
def assoc_recipe(request, event_id):
  recipe_id = request.POST['recipes']
  recipe = Recipe.objects.get(id=recipe_id)
  recipe.events.add(event_id)
  return redirect('events_detail', event_id)

@login_required
def vote_up(request, event_id, recipe_id):
  vote = Vote.objects.filter(event_id=event_id, recipe_id=recipe_id, user=request.user)
  if vote:
    return redirect('events_detail', event_id)
  else:
    Vote.objects.create(event_id=event_id, recipe_id=recipe_id, user=request.user)
    return redirect('events_detail', event_id)

@login_required
def add_photo_group(request, group_id):
  # photo file will be the "name" attribute of the input
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
    s3 = boto3.client('s3')
    # need a unique "key" name for s3
    # and need the same file extension as well
    key = uuid.uuid4().hex[:8] + photo_file.name[photo_file.name.rfind('.'):]
    try:
      bucket = os.environ['S3_BUCKET']
      s3.upload_fileobj(photo_file, bucket, key)
      url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
      PhotoGroup.objects.create(url=url, group_id=group_id)
    except Exception as e:
      print('An error occured uploading file to S3')
      print(e)

  return redirect('detail', group_id=group_id)

@login_required
def add_photo_event(request, event_id):
  # photo file will be the "name" attribute of the input
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
    s3 = boto3.client('s3')
    # need a unique "key" name for s3
    # and need the same file extension as well
    key = uuid.uuid4().hex[:8] + photo_file.name[photo_file.name.rfind('.'):]
    try:
      bucket = os.environ['S3_BUCKET']
      s3.upload_fileobj(photo_file, bucket, key)
      url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
      PhotoEvent.objects.create(url=url, event_id=event_id)
    except Exception as e:
      print('An error occured uploading file to S3')
      print(e)
  return redirect('events_detail', event_id=event_id)

# @login_required
# def add_photo_profile(request, profile_id):
#   # photo file will be the "name" attribute of the input
#   photo_file = request.FILES.get('photo-file', None)
#   if photo_file:
#     s3 = boto3.client('s3')
#     # need a unique "key" name for s3
#     # and need the same file extension as well
#     key = uuid.uuid4().hex[:8] + photo_file.name[photo_file.name.rfind('.'):]
#     try:
#       bucket = os.environ['S3_BUCKET']
#       s3.upload_fileobj(photo_file, bucket, key)
#       url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
#       Photo.objects.create(url=url, cat_id=cat_id)
#     except Exception as e:
#       print('An error occured uploading file to S3')
#       print(e)

#   return redirect('detail', profile_id=profile_id)

@login_required
def add_photo_recipe(request, recipe_id):
  # photo file will be the "name" attribute of the input
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
    s3 = boto3.client('s3')
    # need a unique "key" name for s3
    # and need the same file extension as well
    key = uuid.uuid4().hex[:8] + photo_file.name[photo_file.name.rfind('.'):]
    try:
      bucket = os.environ['S3_BUCKET']
      s3.upload_fileobj(photo_file, bucket, key)
      url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
      PhotoRecipe.objects.create(url=url, recipe_id=recipe_id)
    except Exception as e:
      print('An error occured uploading file to S3')
      print(e)

  return redirect('recipes_index')

