from django.contrib import admin
from .models import Store, Review, Reaction, UserProfile, Follow, Notification, Tag

# Register your models here.
admin.site.register(Store)
admin.site.register(Review)
admin.site.register(Reaction)
admin.site.register(UserProfile)
admin.site.register(Follow)
admin.site.register(Notification)
admin.site.register(Tag)
