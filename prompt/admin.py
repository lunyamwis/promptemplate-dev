from django.contrib import admin
from .models import Prompt,Query, ToneOfVoice, Role,Crew,Task,Agent,Tool
# Register your models here.

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(PromptAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(ToneOfVoice)
class ToneOfVoiceAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ToneOfVoiceAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(RoleAdmin, self).get_form(request, obj, **kwargs)
        return form

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(QueryAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(CrewAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(AgentAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(TaskAdmin, self).get_form(request, obj, **kwargs)
        return form


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ("id",)
        form = super(ToolAdmin, self).get_form(request, obj, **kwargs)
        return form
