from django.shortcuts import render
from django.template.loader import render_to_string

from nova.models import *
from cinder.models import *
from keystone.models import *
from django.db.models import Avg, Count, Min, Sum
from django.db.models.functions import Coalesce
import datetime
from monasca.tasks import influx_query
import pytz
import math

def generate_report(begin_date, end_date):
    context = {}

    sponsors = Sponsors.objects.all()
    for sponsor in sponsors:
        if sponsor.email not in context.keys():
            context[sponsor.email] = []
        projects = sponsor.projects.all()
        for project in projects:
            print(project)
            ## create an dict with project content
            details = {}
            details['header'] = {}
            details['header']['domain'] = project.domain_id.name
            details['header']['project'] = project.name
            details['body'] = {}
            ## resources
            # project is too recently but dont have quotas, we just skip
            try:
                project_quotas = project.quotas.all()[0]
            except:
                continue
            nova_servers = project.servers.filter(created__lte=end_date)
            cinder_volumes = project.volumes.filter(created_at__lte=end_date)
            details['body']['resources'] = []
            # instances
            resource_detail = {}
            resource_detail["name"] = "Instâncias"
            resource_detail["used"] = nova_servers.count()
            resource_detail["reserved"] = project_quotas.instances if project_quotas.instances > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # vcpu
            resource_detail = {}
            resource_detail["name"] = "vCPU"
            # sum all vcpus from a queryset of servers
            resource_detail["used"] = nova_servers.aggregate(sum=Coalesce(Sum('flavor__vcpus'), 0))['sum']
            resource_detail["reserved"] = project_quotas.cores if project_quotas.cores > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # ram
            resource_detail = {}
            resource_detail["name"] = "RAM"
            # sum all ram from a queryset of servers
            resource_detail["used"] = nova_servers.aggregate(sum=Coalesce(Sum('flavor__ram'),1))['sum']
            resource_detail["reserved"] = project_quotas.ram if project_quotas.ram > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # storage
            resource_detail = {}
            resource_detail["name"] = "Armazenamento"
            volumes_storage_used = cinder_volumes.aggregate(sum=Coalesce(Sum('size'), 0))['sum']
            backups_storage_used = cinder_volumes.aggregate(sum=Coalesce(Sum('backup__size'), 0))['sum']
            snapshots_storage_used = cinder_volumes.aggregate(sum=Coalesce(Sum('snapshot_id__size'), 0))['sum']
            resource_detail["used"] = volumes_storage_used + backups_storage_used + snapshots_storage_used
            resource_detail["reserved"] = project_quotas.gigabytes if project_quotas.gigabytes > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # volumes
            resource_detail = {}
            resource_detail["name"] = "Volumes"
            resource_detail["used"] = cinder_volumes.count()
            resource_detail["reserved"] = project_quotas.volumes if project_quotas.volumes > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # backups
            resource_detail = {}
            resource_detail["name"] = "Backups"
            resource_detail["used"] = cinder_volumes.aggregate(sum=Coalesce(Count('backup'), 0))['sum']
            resource_detail["reserved"] = project_quotas.volumes if project_quotas.volumes > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # snapshots
            resource_detail = {}
            resource_detail["name"] = "Snapshots de volume"
            resource_detail["used"] = cinder_volumes.aggregate(sum=Coalesce(Count('snapshot_id'), 0))['sum']
            resource_detail["reserved"] = project_quotas.backups if project_quotas.backups > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # load balancer
            resource_detail = {}
            resource_detail["name"] = "Load Balancers"
            resource_detail["used"] = project_quotas.loadbalancer_used
            resource_detail["reserved"] = project_quotas.loadbalancer_limit if project_quotas.loadbalancer_limit > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            # floating ip
            resource_detail = {}
            resource_detail["name"] = "IPs Flutuante"
            resource_detail["used"] = project_quotas.floatingip_used
            resource_detail["reserved"] = project_quotas.floatingip_limit if project_quotas.floatingip_limit > 0 else  1
            resource_detail["perc_used"] = round((resource_detail["used"] / resource_detail["reserved"]) * 100, 2)
            details['body']['resources'].append(resource_detail)
            ## servers
            details['body']['servers'] = []
            for server in nova_servers:
                begin_datetime = datetime.datetime.fromisoformat(begin_date)
                end_datetime = datetime.datetime.fromisoformat(end_date)

                resource_detail = {}
                resource_detail["name"] = server.name
                resource_detail["flavor"] = server.flavor.name
                # calculate hours used
                resource_detail["hours_used"] = int(math.ceil(total_time(server, begin_datetime, end_datetime).total_seconds() / 60 / 60))
                # build status through actions
                # print(server.name)
                # print(server.actions.values())
                server_status_action = server.actions.values()
                if server_status_action:
                    server_status_action = server_status_action[0]
                    if server_status_action == "pause":
                        resource_detail["status"] = "Ativa (pausada)"
                    elif server_status_action in to_off_states:
                        resource_detail["status"] = "Inativa"
                    elif server_status_action not in to_off_states:
                        resource_detail["status"] = "Ativa"
                else:
                    resource_detail["status"] = "Indefinido"
                # calculate cpu usage
                measurement = "vm.cpu.utilization_norm_perc"
                resource_name = "resource_id"
                resource_id = server.id
                cpu_records = influx_query(measurement, resource_name, resource_id, begin_date=begin_date, end_date=end_date)
                if cpu_records:
                    cpu_avg = 0
                    for cpu in cpu_records:
                        cpu_avg += cpu['_value']
                    resource_detail["cpu_avg"] = round(cpu_avg / len(cpu_records), 2)
                else:
                    resource_detail["cpu_avg"] = 0
                details['body']['servers'].append(resource_detail)
            
            # volumes used
            details['body']['volumes'] = []
            for volume in cinder_volumes:
                resource_detail = {}
                resource_detail['name'] = volume.name
                resource_detail['size'] = volume.size
                details['body']['volumes'].append(resource_detail)
            
            # flavors used
            flavors_list = []
            for server in nova_servers:
                if server.flavor not in flavors_list:
                    flavors_list.append(server.flavor)
            flavors_list = sorted(flavors_list , key = lambda x: x.vcpus)
            details['body']['flavors'] = []
            for flavor in flavors_list:
                resource_detail = {}
                resource_detail['name'] = flavor.name
                resource_detail['vcpus'] = flavor.vcpus
                resource_detail['mem_gb'] = flavor.ram
                resource_detail['disk_size'] = flavor.disk
                details['body']['flavors'].append(resource_detail)
            
            context[sponsor.email].append(details)

    return context


#here we have all the relevant state changes to know if the instance is active or inactive so we can check it later
to_on_states = ['create', 'restore', 'start', 'reboot', 'unpause', 'resume', 'unrescue', 'unshelve', 'pause']
to_off_states = ['softDelete', 'forceDelete', 'delete', 'stop', 'shelve', 'suspend', 'error']


#this function is to calculate the total time of instance use
def total_time(server, start_date, end_date):
    #first we need an accumulator
    total = datetime.timedelta(days = 0)
    '''
    the algorithm here is to go through all the actions taken by the instance and always look back
    to see if we need to increase the time of using the instance, if the instance was created 
    before the initial consultation date and is turned on when the initial date is exceeded, we will
    also need to increase the time from this date until the first action taken within the consulted
    time interval or until the end date of the consultation
    '''
    on = False
    last = start_date
    for action in server.actions.all().order_by('start_time'):
        date = action.start_time
        
        if date > end_date:
            break

        if date >= start_date:
            if on:
                total += date - last
            last = date
        
        if action.action not in to_off_states:
            on = True
        elif action.action in to_off_states:
            on = False
    
    if on:
        total += end_date - last
    
    return total


def my_view():
    """
    generate html report
    """
    context = generate_report()
    for sponsor in context:
        new_context = {}
        new_context['context'] = context[sponsor]
        content = render_to_string('user_report_template.html', new_context)
        filename = "%s.html" % sponsor
        with open(filename, 'w', encoding="utf-8") as static_file:
            static_file.write(content)


