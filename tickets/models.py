from django.db import models
from django.contrib.auth.models import User

DEPARTMENT_CHOICES = [
    ('Admin', 'Admin'),
    ('Finance', 'Finance'),
    ('MIS', 'MIS'),
    ('Operational/General Management', 'Operational/General Management'),
    ('Human Resources', 'Human Resourcres'),
    ('Security', 'Security'),
]

CATEGORY_CHOICES = [
    ('Desktop Publishing/Application Support', 'Desktop Publishing/Application Support'),
    ('Coaching Supprot/Set-up Assistance/ Trainings','Coaching Supprot/Set-up Assistance/ Trainings'),
    ('Internal & Web-based System Concerns', 'Internal & Web-based System Concerns'),
    ('Website Access Request', 'Website Access Request'),
    ('Others (Pls. Specify)','Others (Pls Specify)'),

]
SUBCATEGORY_CHOICES = [
    #Desktop Publishing
    ('Graphics Layout/Photo Editing', 'Graphics Layout/Photo Editing'),
    ('MS Word / Excel / Powerpoint / Visio Formatting', 'MS Word / Excel / Powerpoint / Visio Formatting'),

    # Coaching Support
    ('IT Devices / Hardware', 'IT Devices / Hardware'),
    ('Software Applications', 'Software Applications'),
    ('Equipment / Devices', 'Equipment / Devices'),
    ('Technical Services', 'Technical Services'),

    # Internal & Web-based
    ('Data Correction / Amendments', 'Data Correction / Amendments'),
    ('Opascor Terminal Operating System (OpTOS)', 'Opascor Terminal Operating System (OpTOS)'),
    ('OpTOS Blockcontrol', 'OpTOS Blockcontrol'),
    ('OpTOS Reefer', 'OpTOS Reefer'),
    ('OpTOS Analytics', 'OpTOS Analytics'),
    ('OpTOS Weighing', 'OpTOS Weighing'),

    # Website Access
    ('Internet Access Schedule', 'Internet Access Schedule'),

    # Others
    ('Others - Please Specify', 'Others - Please Specify'),

]

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('In Progress', 'In Progress'),
    ('Resolved', 'Resolved'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.department}"

class Concern(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    sub_category = models.CharField(max_length=200, choices=SUBCATEGORY_CHOICES)
    description = models.TextField()
    others_specify = models.CharField(max_length=255, blank=True)  # for "Others - Please Specify"
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    remarks = models.CharField(max_length=255, blank=True)
    assigned_to = models.CharField(max_length=100, blank=True)
    date_submitted = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Concern #{self.id} - {self.user.username}"
    def __str__(self):
        return f"Concern #{self.id} - {self.user.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} - {self.subject}"

# Create your models here.
from django.db.models.signals import post_save

# Create your models here.
from django.db.models.signals import post_save
from django.dispatch import receiver

 
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.is_admin = instance.is_staff
        instance.userprofile.save()
    else:
        # Auto-create profile for superusers/staff with no profile
        if instance.is_staff or instance.is_superuser:
            UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'department': 'Admin',
                    'is_admin': True
                }
            )
