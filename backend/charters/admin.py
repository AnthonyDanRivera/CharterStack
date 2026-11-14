from django.contrib import admin

from .models import Bus, Contract, DemoSession, Driver, Terminal, TripUnit, ZipCode


@admin.register(DemoSession)
class DemoSessionAdmin(admin.ModelAdmin):
    list_display = ["short_id", "user", "created_at"]
    readonly_fields = ["short_id", "user", "created_at", "ip_hash"]
    list_select_related = ["user"]


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "phone"]


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ["number", "terminal", "seats", "model", "has_wc_lift", "is_active"]
    list_filter = ["terminal", "is_active", "has_wc_lift", "seats"]
    search_fields = ["number", "model"]


@admin.register(ZipCode)
class ZipCodeAdmin(admin.ModelAdmin):
    list_display = ["zip", "city", "state", "county"]
    list_filter = ["state"]
    search_fields = ["zip", "city", "county"]


class TripUnitInline(admin.TabularInline):
    model = TripUnit
    extra = 0
    fields = [
        "unit_number",
        "is_duplicate",
        "driver",
        "bus",
        "report_time",
        "status",
        "confirm_initials",
    ]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "number",
        "owner",
        "status",
        "organization",
        "begin_date",
        "bus_count",
        "terminal",
        "total_price",
    ]
    list_filter = ["status", "terminal"]
    search_fields = ["number", "organization", "group_name", "owner__username"]
    list_select_related = ["owner", "terminal"]
    inlines = [TripUnitInline]


@admin.register(TripUnit)
class TripUnitAdmin(admin.ModelAdmin):
    list_display = ["__str__", "owner", "driver", "bus", "report_time", "status"]
    list_filter = ["status", "is_duplicate"]
    search_fields = ["contract__number", "owner__username"]
    list_select_related = ["contract", "owner", "driver", "bus"]
