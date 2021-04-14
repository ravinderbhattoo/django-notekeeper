from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from .models import Note, AddFileForm, NoteFile
from django.contrib import messages
import json, os
from datetime import datetime, timedelta 
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.core.signing import BadSignature
from taggit.models import Tag
 
def edit_note_files(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if (note.user != request.user) and (request.user.username not in note.shared):
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    if request.method == 'POST':
        form = AddFileForm(request.POST, request.FILES)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.note = note
            form_data.save()
            return redirect('note_detail', slug=note.slug)
        else:
            messages.error(request, 'Note valid file.')
            return redirect('note_detail', slug=note.slug)
    else:
        form = AddFileForm(initial={
            'note': note,
        })
        return render(request, 'modals/edit_files.html', {'form': form, 'note': note})

def confirm_delete_file(request, pk, fk):
    note = get_object_or_404(Note, pk=pk)
    file = get_object_or_404(NoteFile, pk=fk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    context = {
        'id': "delete_file_confirmation",
        'data': file.file,
        'url0': "delete_file",
        'itemid': file.id,
        }
    return render(request, 'modals/delete_confirm.html', context)
    
def delete_file(request, fk):
    file = get_object_or_404(NoteFile, pk=fk)
    if file.note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('note_detail', slug=note.slug)
    file.delete()
    messages.success(request, 'File deleted successfully!')
    return redirect('note_detail', slug=file.note.slug)

