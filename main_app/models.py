import email
from tokenize import group
from django.db import models
from django.urls import reverse
from datetime import date, datetime
# Import the User
from django.contrib.auth.models import User

class Profile(models.Model):
    name = models.CharField(max_length=50)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{ self.name }'

class Group(models.Model):
    name=models.CharField(max_length=50)
    description=models.TextField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    leader = models.CharField(max_length=50)

    members = models.ManyToManyField(Profile)
    

    def __str__(self):
        return f'{self.name} ({self.id})'
    
    def get_absolute_url(self):
        return reverse('index')


class Event(models.Model):
    title = models.CharField(max_length=100)
    host = models.CharField(max_length=100) # potential to change to dropdown(Group Members)
    location = models.CharField(max_length=100)
    datetime = models.DateTimeField()

    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.group}'s event on {self.datetime}"


    # leader_username = models.CharField(max_length=50)
    # members = models.ManyToManyField(User)

class Recipe(models.Model):
    title = models.CharField(max_length=50)
    url = models.URLField(max_length=300)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    events = models.ManyToManyField(Event)
    
    def get_absolute_url(self):
        return reverse('recipes_index')
    
    def __str__(self):
        return f'{self.title}'

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

class PhotoGroup(models.Model):
  url = models.CharField(max_length=200)
  group = models.ForeignKey(Group, on_delete=models.CASCADE)
  
  def __str__(self):
    return f"photo for group_id: {self.group_id} @{self.url}"

class PhotoEvent(models.Model):
  url = models.CharField(max_length=200)
  event = models.ForeignKey(Event, on_delete=models.CASCADE)
  
  def __str__(self):
    return f"photo for event_id: {self.event_id} @{self.url}"

class PhotoRecipe(models.Model):
  url = models.CharField(max_length=200)
  recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
  
  def __str__(self):
    return f"photo for recipe_id: {self.recipe_id} @{self.url}"

class PhotoProfile(models.Model):
  url = models.CharField(max_length=200)
  profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
  
  def __str__(self):
    return f"photo for profile_id: {self.profile_id} @{self.url}"