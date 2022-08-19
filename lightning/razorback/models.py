from django.db import models

class Link(models.Model):
    id = models.AutoField(primary_key=True)
    point_b = models.URLField(max_length=512)
    point_a = models.ForeignKey('Link', null=True, related_name="Point_A", on_delete=models.SET_NULL)
    visited = models.BooleanField(default=False)
    content = models.TextField(default="", null=True)
    taken = models.BooleanField(default=False, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ('point_a', 'point_b')
