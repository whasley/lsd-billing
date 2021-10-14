import os

from celery import Celery
from celery.schedules import crontab
from core.conf import conf_file

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(['keystone', 'cinder', 'nova', 'monasca'])

openstack_timer = "*/%d" % conf_file['openstack']['collect_period']
monasca_timer = "*/%d" % conf_file['monasca']['collect_period']

app.conf.beat_schedule = {
    # cinder
    # "cinder_save_volumes":{
    #     "task": "cinder.tasks.save_volumes",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "cinder_save_backups":{
    #     "task": "cinder.tasks.save_backups",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "cinder_save_snapshots":{
    #     "task": "cinder.tasks.save_snapshots",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # # keystone
    # "keystone_save_domains": {
    #     "task": "keystone.tasks.save_domains",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "keystone_save_projects_and_sponsors": {
    #     "task": "keystone.tasks.save_projects_and_sponsors",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "keystone_save_services": {
    #     "task": "keystone.tasks.save_services",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "keystone_save_regions": {
    #     "task": "keystone.tasks.save_regions",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "keystone_save_quotas": {
    #     "task": "keystone.tasks.save_quotas",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # # nova
    # "nova_save_services": {
    #     "task": "nova.tasks.save_services",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "nova_save_hypervisors": {
    #     "task": "nova.tasks.save_hypervisors",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "nova_save_aggregates": {
    #     "task": "nova.tasks.save_aggregates",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "nova_save_flavors": {
    #     "task": "nova.tasks.save_flavors",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "nova_save_servers": {
    #     "task": "nova.tasks.save_servers",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # "nova_save_instance_actions": {
    #     "task": "nova.tasks.save_instance_actions",
    #     "schedule": crontab(minute=openstack_timer),
    # },
    # monasca
    "monasca_schedule_save_statistics": {
        "task": "monasca.tasks.schedule_save_statistics",
        "schedule": crontab(minute=monasca_timer),
    },
}
