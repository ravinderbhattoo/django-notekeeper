from django.db import models
from django import forms
from django.shortcuts import redirect
from django.utils.text import slugify
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.core.signing import Signer
from django.utils.html import mark_safe
import markdown
import uuid
from django.urls import reverse
from unidecode import unidecode
import markdown.extensions.fenced_code
import markdown.extensions.codehilite
import markdown.extensions.tables
import markdown.extensions.toc
from django_cryptography.fields import encrypt
import csv
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot


def generate_unique_slug(_class, field):
    """
        return unique slug if origin slug is exist.
        eg: `foo-bar` => `foo-bar-1`
        :param `field` is specific field for title.
    """
    origin_slug = slugify(field)
    unique_slug = origin_slug
    numb = 1
    while _class.objects.filter(slug=unique_slug).exists():
        unique_slug = '%s-%d' % (origin_slug, numb)
        numb += 1
    return unique_slug

def csv2table(filename, sep, header):
    return pd.read_csv(filename, sep=sep, header=header).iloc[:100].to_html(col_space=50, classes=['table table-striped table-bordered'])

def get_plot_div(filename, sep, header, ptype, *args):
    df = pd.read_csv(filename, sep=sep, header=header)
    df.columns = [str(i) for i in df.columns]
    data = [df[i].values for i in args if "=" not in i]
    kwargs = [i for i in args if "=" in i]
    dict1 = {}
    for i in kwargs:
        a, b = i.split('=')
        try:
            b = float(b)
        except:
            pass
        dict1[a] = b
    names = ['x', 'y', 'z']
    indata = {}
    for ind,x in enumerate(data):
        indata[names[ind]] = x
    return plotly_plot(ptype, indata, names)

def plotly_plot(func, indata, names):
    mode = "none"
    if func == "Line":
        func = "Scatter"
        mode = "lines"
    elif func == "Scatter":
        mode = "markers"
    if func in ["Histogram", "Bar"]:
        trace1 = go.__getattr__(func)(indata)
    else:
        trace1 = go.__getattr__(func)(indata, mode=mode)
    data = [trace1]
    Axis = dict(xaxis = {'title':names[0]})
    if len(names)>1:
        Axis.update(dict(yaxis = {'title':names[1]}))
    layout = go.Layout(**Axis,
        width=500,
        height=500,
    )

    fig = go.Figure(data=data, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div

def fix_image(content):
    contents = content.split('\n')
    out = []
    for line in contents:
        if line[:6] == "?image":
            url = line[7:].strip()
            line = "<div style='border: 1px solid black; width:auto; display:inline-block;margin-top: 10px; margin-bottom: 20px'>{0}<br>\n<img src=/media/attachments/{0} style='height:400px;width:auto;border: 1px solid black;'><br></div>".format(url)
            out += ["<br>"+line+"<br>"]
        elif line[:4] == "?csv":
            try:
                try:
                    url, sep, header = line[5:].strip().split()
                    try:
                        header = int(header)
                    except:
                        header = None
                except:
                    url, sep, header = line[5:].strip(), ",", 0
                out += ["<br>" + "<div style='padding-bottom: 1cm; border: 1px solid red;width: 100%;max-height: 500px;overflow: auto;'>"]+[csv2table("media/attachments/"+url, sep, header)]+["</div>"+"<br>"]
            except:
                out += [f"Unable to show csv file ({url}) inline."] 
        elif line[:5] == "?plot":
            try:
                url, sep, header, ptype, *args = line[5:].strip().split()
                try:
                    header = int(header)
                except:
                    header = None
                out += ["<br><div style='border: 1px solid black; width:auto; display:inline-block;margin-top: 10px; margin-bottom: 20px'>"+get_plot_div("media/attachments/"+url, sep, header, ptype, *args)+"</div><br>"]
            except:
                out += [f"Unable to show plot ({url}) inline."] 
        elif line[:5] == "?code":
            try:
                url = line[5:].strip()
                with open("media/attachments/"+url, "r") as f:
                    out += ["<br>\n```\n"] + f.readlines() + ["\n```\n<br>"]
            except:
                out += [f"Unable to show code ({url}) inline."] 
        else:
            out += [line]
    return "\n".join(out)

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note_title = models.CharField(max_length=200)
    note_content = encrypt(models.TextField(null=True, blank=True))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.CharField(max_length=20, default="Notes")
    timeline = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    shared = models.CharField(default="", max_length=200, blank=True)
    slug = models.SlugField(max_length=200, unique=True)
    tags = TaggableManager()
    signer = Signer(salt='notes.Note')

    def get_message_as_markdown(self):
        return mark_safe(
            markdown.markdown(
                fix_image(self.note_content),
                extensions=['codehilite', 'fenced_code', 'markdown_checklist.extension', 'tables', 'toc'],
                # extension_configs={
                #     'codehilite':{
                #         'linenums': True
                #     }
                # }
                output_format="html5"
            )
        )

    def get_signed_hash(self):
        signed_pk = self.signer.sign(self.pk)
        return signed_pk

    def get_absolute_url(self):
        return reverse('share_notes', args=(self.get_signed_hash(),))

    def __str__(self):
        return self.note_title

    def save(self, *args, **kwargs):
        title = unidecode(self.note_title)
        if self.slug:
            if slugify(title) != self.slug:
                self.slug = generate_unique_slug(Note, title)
        else:
            self.slug = generate_unique_slug(Note, title)
        super(Note, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from attachments.models import NoteFile
        files = NoteFile.objects.filter(note=self)
        for file in files:
            file.delete()
        super(Note, self).delete(*args, **kwargs)
        


class AddNoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = '__all__'
        exclude = ['slug', 'user']
        widgets = {
            'tags': forms.TextInput(
                attrs={
                    'data-role':'tagsinput',
                }
            ),
        }
    

    


