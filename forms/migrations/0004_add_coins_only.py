# Generated manually - Add coins field to Profile model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0003_alter_fooditem_options_alter_form_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='coins',
            field=models.IntegerField(default=0, help_text='Number of reward coins earned by the user'),
        ),
    ] 