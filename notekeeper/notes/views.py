from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from .models import Note, AddNoteForm
from attachments.models import NoteFile
from django.contrib.auth.models import User

from django.contrib import messages
import json, os
from datetime import datetime, timedelta 
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.signing import BadSignature
from taggit.models import Tag

# for zip downloads
import os
import zipfile
from io import BytesIO
from django.http import HttpResponse

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    # use short variable names
    sUrl = settings.STATIC_URL      # Typically /static/
    sRoot = settings.STATIC_ROOT    # Typically /home/userX/project_static/
    mUrl = settings.MEDIA_URL       # Typically /static/media/
    mRoot = settings.MEDIA_ROOT     # Typically /home/userX/project_static/media/

    # convert URIs to absolute system paths
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri  # handle absolute uri (ie: http://some.tld/foo.png)

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path


def render_to_pdf(template_src, context_dict={}):
    '''
        Helper function to generate pdf from html
    '''
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Error Rendering PDF", status=400)

def generate_zip(request, slug):
    note = get_object_or_404(Note, slug=slug)
    if note.user != request.user and (request.user.username not in note.shared) and not(note.public):
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('note_detail', slug=note.slug)
    files = NoteFile.objects.filter(note=note)
    context = {
        'files' : files,
        'note': note,
    }
    htmlfile = render(request, 'note_only.html', context).content
    temp_file = "media/cache/temp_html.html"
    with open(temp_file, "wb") as f:
        f.write(htmlfile)

    # Files (local path) to put in the .zip
    # FIXME: Change this (get paths from DB etc)
    filenames = ["media/"+f.file.name for f in files]

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    # FIXME: Set this to something better
    zip_subdir = "media/attachments"
    zip_filename = "%s.zip" % note.note_title

    # Open BytesIO to grab in-memory ZIP contents
    s = BytesIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = os.path.join(zip_subdir, fname)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    zf.write(temp_file, "Note.html")

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp

def generate_timeline_zip(request, proj):
    # Filter posts by tag name  
    all_notes = Note.objects.filter(project=proj, user=request.user, timeline=True).order_by('-created_at')
    dict1 = {}
    filenames = []
    for note in all_notes:
        dict1[note] = NoteFile.objects.filter(note=note) 
        for f in dict1[note]:
            filenames += [f.file]
    add_note_form = AddNoteForm()
    context = {
        'proj':proj,
        'all_notes':all_notes,
        'attachs': dict1,
        'add_note_form': add_note_form
    }
    htmlfile = render(request, 'timeline_only.html', context).content
    temp_file = "media/cache/temp_html.html"
    with open(temp_file, "wb") as f:
        f.write(htmlfile)

    # Files (local path) to put in the .zip
    # FIXME: Change this (get paths from DB etc)
    filenames = ["media/"+f.name for f in filenames]

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    # FIXME: Set this to something better
    zip_subdir = "media/attachments"
    zip_filename = "%s.zip" % note.note_title

    zip_filename = f"Timeline-{proj}"
    # Open BytesIO to grab in-memory ZIP contents
    s = BytesIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = os.path.join(zip_subdir, fname)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    zf.write(temp_file, "Timeline.html")

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


def generate_pdf(request, slug):
    note = get_object_or_404(Note, slug=slug)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    notes = Note.objects.filter(user=request.user).order_by('-updated_at')
    add_note_form = AddNoteForm()
    context = {
        'note_detail': note,
    }
    pdf = render_to_pdf('note_as_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "{}.pdf".format(note.slug)
        content = "inline; filename={}".format(filename)
        content = "attachment; filename={}".format(filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")


def home(request):
    if request.user.is_authenticated:
        notes = Note.objects.filter(user=request.user).order_by('-updated_at')
        all_notes = Note.objects.filter(user=request.user).order_by('-updated_at')
        dict1 = {}
        for note in all_notes:
            dict1[note] = NoteFile.objects.filter(note=note) 
        projects = [i.project for i in notes]
        projects = list(set(projects))
        projects.sort()
        # paginator = Paginator(all_notes, 15)

        if request.method == 'POST':
            form = AddNoteForm(request.POST, request.FILES)
            if form.is_valid():
                form_data = form.save(commit=False)
                form_data.user = request.user
                form_data.save()
                # Without this next line the tags won't be saved.
                form.save_m2m()
                form = AddNoteForm()
                messages.success(request, 'Note added successfully!')
                return redirect('notes')
        else:
            form = AddNoteForm()
        context = {
            'notes': notes,
            'projects':projects,
            'attachs': dict1,
            'all_notes': all_notes,
            'add_note_form': form,
            'script_name': request.META['SCRIPT_NAME'],
        }
        return render(request, 'notes.html', context)
    else:
        return render(request, 'index.html')


def get_note_details(request, slug):
    note = get_object_or_404(Note, slug=slug)
    if request.user.is_authenticated:
        if (note.user != request.user) and (request.user.username not in note.shared) and not(note.public):
            messages.error(request, 'You are not authenticated to perform this action')
            return redirect('notes')
        notes = Note.objects.filter(user=request.user).order_by('-updated_at')
        files = NoteFile.objects.filter(note=note)
        projects = [i.project for i in notes]
        projects = list(set(projects))
        projects.sort()

        add_note_form = AddNoteForm()
        absolute_url = request.build_absolute_uri(note.get_absolute_url())
        context = {
            'notes': notes,
            'files' : files,
            'projects':projects,
            'note': note,
            'add_note_form': add_note_form,
            'absolute_url': absolute_url
        }
        return render(request, 'note_details.html', context)
    else:
        return get_note_details_public(request, slug)

def get_note_details_public(request, slug):
    note = get_object_or_404(Note, slug=slug)
    notes = Note.objects.filter(public=True).order_by('-updated_at')
    files = NoteFile.objects.filter(note=note)
    projects = [i.project for i in notes]
    projects = list(set(projects))
    projects.sort()

    add_note_form = AddNoteForm()
    absolute_url = request.build_absolute_uri(note.get_absolute_url())
    context = {
        'notes': notes,
        'files' : files,
        'projects':projects,
        'note': note,
        'add_note_form': add_note_form,
        'absolute_url': absolute_url
    }
    return render(request, 'note_only.html', context)


def edit_note_details(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if (note.user != request.user) and (request.user.username not in note.shared):
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    if request.method == 'POST':
        form = AddNoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form_data = form.save(commit=False)
            if form_data.shared == "None, ":
                form_data.user = request.user
            else:
                form_data.user = note.user
            form_data.save()
            form.save_m2m()
            return redirect('note_detail', slug=note.slug)
    else:
        form = AddNoteForm(initial={
            'note_title': note.note_title,
            'note_content': note.note_content,
            'tags': ','.join([i.slug.replace('_1', '') for i in note.tags.all()]),
        }, instance=note)
        return render(request, 'modals/edit_note_modal.html', {'form': form})


def confirm_delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    context = {
        'id': "delete_note_confirmation",
        'data': note.note_title,
        'url0': "delete_note",
        'itemid': note.id,
    }
    return render(request, 'modals/delete_confirm.html', context)
    
def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    note.delete()
    messages.success(request, 'Note deleted successfully!')
    return redirect('notes')


def search_note(request):
    if request.is_ajax():
        q = request.GET.get('term')
        notes = Note.objects.filter(
                note_title__icontains=q,
                user=request.user
            )[:10]
        results = []
        for note in notes:
            note_json = {}
            note_json['slug'] = note.slug
            note_json['label'] = note.note_title
            note_json['value'] = note.note_title
            results.append(note_json)
        data = json.dumps(results)
    else:
        note_json = {}
        note_json['slug'] = None
        note_json['label'] = None
        note_json['value'] = None
        data = json.dumps(note_json)
    return HttpResponse(data)


def get_shareable_link(request, signed_pk):
    try:
        pk = Note.signer.unsign(signed_pk)
        note = Note.objects.get(pk=pk)
        context = {
            'note_detail': note
        }
        return render(request, 'shared_note.html', context)
    except (BadSignature, Note.DoesNotExist):
        raise Http404('No Order matches the given query.')


def get_all_notes_tags(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    # Filter posts by tag name  
    all_notes = Note.objects.filter(tags=tag, user=request.user)
    notes = Note.objects.filter(user=request.user).order_by('-updated_at')
    projects = [i.project for i in notes]
    projects = list(set(projects))
    projects.sort()
    add_note_form = AddNoteForm()
    context = {
        'tag':tag,
        'all_notes':all_notes,
        'notes': notes,
        'projects':projects,
        'add_note_form': add_note_form
    }
    return render(request, 'tags.html', context)

def get_timeline_proj(request, proj):
    # Filter posts by tag name  
    all_notes = Note.objects.filter(project=proj, user=request.user).order_by('-created_at')
    dict1 = {}
    for note in all_notes:
        dict1[note] = NoteFile.objects.filter(note=note) 
    notes = Note.objects.filter(user=request.user).order_by('-updated_at')
    projects = [i.project for i in notes]
    projects = list(set(projects))
    projects.sort()
    add_note_form = AddNoteForm()
    context = {
        'proj':proj,
        'all_notes':all_notes,
        'attachs': dict1,
        'notes': notes,
        'projects':projects,
        'add_note_form': add_note_form
    }
    return render(request, 'timeline.html', context)

def get_proj(request, proj):
    # Filter posts by tag name  
    all_notes = Note.objects.filter(user=request.user, project=proj)
    notes = Note.objects.filter(user=request.user).order_by('-updated_at')
    dict1 = {}
    for note in all_notes:
        dict1[note] = NoteFile.objects.filter(note=note) 
    projects = [proj]
    add_note_form = AddNoteForm()
    context = {
        'all_notes':all_notes,
        'notes': notes,
        'attachs': dict1,
        'projects':projects,
        'add_note_form': add_note_form
    }
    return render(request, 'project.html', context)

def projects(request):
    if request.user.is_authenticated:
        # Filter posts by tag name  
        all_notes = Note.objects.filter(user=request.user)
        notes = Note.objects.filter(user=request.user).order_by('-updated_at')
        dict1 = {}
        for note in all_notes:
            dict1[note] = NoteFile.objects.filter(note=note) 
        projects = [i.project for i in notes]
        projects = list(set(projects))
        projects.sort()
        add_note_form = AddNoteForm()
        context = {
            'all_notes':all_notes,
            'notes': notes,
            'attachs': dict1,
            'projects':projects,
            'add_note_form': add_note_form
        }
        return render(request, 'projects.html', context)
    else:
        return redirect('public')


def public_projects(request):
        # Filter posts by tag name  
        all_notes = Note.objects.filter(public=True)
        notes = Note.objects.filter(public=True).order_by('-updated_at')
        dict1 = {}
        for note in all_notes:
            dict1[note] = NoteFile.objects.filter(note=note) 
        projects = [i.project for i in notes]
        projects = list(set(projects))
        projects.sort()
        add_note_form = AddNoteForm()
        context = {
            'all_notes':all_notes,
            'notes': notes,
            'attachs': dict1,
            'projects':projects,
            'add_note_form': add_note_form
        }
        return render(request, 'public_projects.html', context)

def shared(request):
    if request.user.is_authenticated:
        # Filter posts by tag name  
        all_notes = Note.objects.filter(user=request.user)
        notes = Note.objects.filter(shared__icontains=request.user).order_by('-updated_at')
        add_note_form = AddNoteForm()
        context = {
            'all_notes':all_notes,
            'notes': notes,
            'add_note_form': add_note_form
        }
        return render(request, 'shared.html', context)
    else:
        return render(request, 'index.html')

def confirm_delete_account(request):
    context = {
        'id': "delete_account_confirmation",
        'data': request.user,
        'url0': "delete_account",
        'itemid': request.user,
    }
    return render(request, 'modals/delete_confirm.html', context)

def delete_account(request, username):
    none_user, _ = User.objects.get_or_create(username="none")
    if request.user.username not in ["none", "admin", "root"]:
        for note in Note.objects.filter(user=request.user):
            if note.public:
                note.user = none_user
                note.save()
            else:
                note.delete()
        request.user.delete()
        messages.success(request, f"Account ({request.user.username}) delete successfully.")
        return redirect('home')
    else:
        messages.error(request, f"This user not allowed to self delete.")
        return redirect('home')

