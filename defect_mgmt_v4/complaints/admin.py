from django.contrib import admin
from .models import Complaint, DefectCategory, ComplaintUpdate, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'phone']
    list_filter  = ['role']


@admin.register(DefectCategory)
class DefectCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'suggested_role', 'color', 'icon']


class UpdateInline(admin.TabularInline):
    model = ComplaintUpdate
    extra = 0
    readonly_fields = ['created_at', 'updated_by']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display  = ['complaint_id', 'title', 'product_name', 'defect_category',
                     'status', 'priority', 'raised_by', 'assigned_to', 'created_at']
    list_filter   = ['status', 'priority', 'defect_category']
    search_fields = ['complaint_id', 'title', 'product_name']
    readonly_fields = ['complaint_id', 'created_at', 'updated_at']
    inlines       = [UpdateInline]


from .models import Reward

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display  = ['user', 'complaint', 'amount', 'awarded_at', 'is_seen']
    list_filter   = ['is_seen', 'awarded_at']
    search_fields = ['user__username', 'complaint__complaint_id']
    readonly_fields = ['awarded_at']
