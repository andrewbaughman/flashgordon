from django.db import models

class Link(models.Model):
    id = models.AutoField(primary_key=True)
    point_b = models.URLField(max_length=200)
    point_a = models.ForeignKey('Link', null=True, related_name="Point_A", on_delete=models.SET_NULL)
    visited = models.BooleanField(default=False)
