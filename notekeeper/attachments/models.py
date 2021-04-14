from django.db import models
from django import forms
from notes.models import Note

class NoteFile(models.Model):
    file = models.FileField(upload_to="attachments/")
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='files')

    def delete(self, *args, **kwargs): 
        self.file.delete()       
        super(NoteFile, self).delete(*args, **kwargs)
    
class AddFileForm(forms.ModelForm):
    class Meta:
        model = NoteFile
        fields = ['file']