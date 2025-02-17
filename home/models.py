from django.db import models

# Create your models here.

class TriviaQuestion(models.Model):
	question_text = models.CharField(max_length=200)
	pub_date = models.DateTimeField('date published')
	answer = models.CharField(max_length=200)
	option1 = models.CharField(max_length=200)
	option2 = models.CharField(max_length=200)
	option3 = models.CharField(max_length=200)
	option4 = models.CharField(max_length=200)

def __str__(self):
	return self.question_text

class Visit(models.Model):
	timestamp = models.DateTimeField(auto_now_add=True)
	path = models.CharField(max_length=255)
	ip = models.GenericIPAddressField()
	
	class Meta:
		ordering = ['-timestamp']
