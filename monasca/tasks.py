import datetime
from django.conf import settings
from django.utils.timezone import now
from celery import shared_task
from monascaclient import client as monasca_client
from decouple import config
from core.conf import conf_file
from nova.models import Hypervisors, Servers


monasca = monasca_client.Client(
    api_version=config("MONASCA_API_VERSION"),
    session=settings.OPENSTACK_SESSION,
    endpoint=config("MONASCA_ENDPOINT"),
    interface=config("MONASCA_INTERFACE"),
)


def influx_query(measurement, resource_name, resource_id):
    """
    funciona como uma facade, retorna uma consulta no influxdb
    """
    bucket_name = config("INFLUX_BUCKET")
    # pega os dados apenas da ultima hora
    start = '-720m'
    from_bucket = ('from(bucket:"%s")' % bucket_name)
    start_date = (' |> range(start: %s)' % start)
    filter_measurement = (' |> filter(fn:(r) => r._measurement == "%s")' % measurement)
    filter_resource = (' |> filter(fn:(r) => r.%s == "%s")' % (resource_name, resource_id))

    query = from_bucket + start_date + filter_measurement + filter_resource
    points = settings.INFLUX_CLIENT.query_api().query(query)

    result = []
    for table in points:
        for row in table.records:
            result.append(row.values)

    return result


@shared_task
def schedule_save_statistics() -> None:
    """
    Collect all metrics declared in yaml configuration file.

    Sera a funcao no schedule beat responsavel por disparar todas as tasks que vao coletar no monasca

    cada funcao dessa sera responsavel por coletar a metrica de apenas uma instancia de um tenant

    a task sempre vai consultar o influx antes, o start_time da coleta sera o ultimo dado do influxdb
    o end_time sera o o datetime.now()
    
    nao me importamos se tivermos duas tasks na fila para o mesmo periodo de tempo, ja que
    posteriormente isso sera resolvido e a fila anda

    o type,name e period da metrica sera recuperado atraves do arquivo de configuracao

    o tenant_name sera consultado direto na database django, assim como o nome de cada instancia ativa
    ambos serao incorporados no atributo dimensions
    """
    # servers = Servers.objects.all().values()

    # statistics_list = conf_file['monasca']['statistics'][0]['name']
    # resource_name = conf_file['monasca']['statistics'][0]['dimension']

    for statistic_definition in conf_file['monasca']['statistics']:
        statistics_list = statistic_definition['name']
        resource_name = statistic_definition['dimension']

        if resource_name == "resource_id":
            resource_objects = Servers.objects.all().values()
        elif resource_name == "hostname":
            resource_objects = Hypervisors.objects.all().values()

        for statistic_name in statistics_list:
            for resource in resource_objects:
                # check the date which metrics begin, if not found, begin save from now
                date_influx = influx_query(
                    measurement=statistic_name,
                    resource_name=resource_name,
                    resource_id=str(resource['id'])
                )
                if not date_influx:
                    start_date = now() - datetime.timedelta(minutes=1)
                else:
                    start_date = date_influx[-1]['_time']

                # define which metrics must be saved
                name = statistic_name
                dimensions = {
                    # "vm_name": server['id'],
                    # "tenant_name": server['tenant_id_id']
                    "resource_id": str(resource['id'])
                }
                metric_type = statistic_definition['type']
                start_time = start_date.isoformat(' ', 'seconds')
                end_time = now().isoformat(' ', 'seconds')
                period = statistic_definition['period']

                save_statistics(name, dimensions, metric_type, start_time, end_time, period)


def save_statistics(name, dimensions, metric_type, start_time, end_time, period):
    """
    Save a statistic from Monasca on InfluxDB.
    """
    statistics = monasca.metrics.list_statistics(
        name=name,
        dimensions=dimensions,
        statistics=metric_type,
        start_time=start_time,
        end_time=end_time,
        period=period,
    )

    statistics_to_save = []
    if not len(statistics):
        print('Not Found')
        return

    statistics = statistics[0]
    for statistic in statistics['statistics']:
        statistic_point = {}
        statistic_point['measurement'] = statistics['name']
        statistic_point['tags'] = statistics['dimensions']
        statistic_point['fields'] = {}
        statistic_point['fields']['value'] = float(statistic[1])
        statistic_point['time'] = statistic[0]
        statistics_to_save.append(statistic_point)

    settings.INFLUX_CLIENT.write_api().write(bucket='monasca', record=statistics_to_save)
