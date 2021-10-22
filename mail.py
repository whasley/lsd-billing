from django.core.mail import EmailMessage
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.conf import settings


def send_templated_mail():
    subject = 'Subject'
    context = {
        "context": [
        {
            "header": {
                "month": "Setembro de 2021",
                "domain": "LSD",
                "project": "Shylock",
                "mem_total": 243540,
                "cpu_total": 121770,
                "cpu_avg": 6.81
            },
            "body": {
                "resources": [
                    {
                        "name": "Instâncias",
                        "used": 7,
                        "reserved": 12,
                        "perc_used": 58.33
                    },
                    {
                        "name": "vCPU",
                        "used": 27,
                        "reserved": 32,
                        "perc_used": 84.38
                    },
                    {
                        "name": "RAM",
                        "used": 54,
                        "reserved": 64,
                        "perc_used": 84.38
                    },
                    {
                        "name": "Armazenamento",
                        "used": 670,
                        "reserved": 1000,
                        "perc_used": 67.00
                    },
                    {
                        "name": "Volumes",
                        "used": 4,
                        "reserved": 12,
                        "perc_used": 33.33
                    },
                    {
                        "name": "Backups",
                        "used": 0,
                        "reserved": 12,
                        "perc_used": 0
                    },
                    {
                        "name": "Snapshots de volume",
                        "used": 0,
                        "reserved": 12,
                        "perc_used": 0
                    },
                    {
                        "name": "Load Balancers",
                        "used": 0,
                        "reserved": 4,
                        "perc_used": 0
                    },
                    {
                        "name": "IPs Flutuante",
                        "used": 2,
                        "reserved": 8,
                        "perc_used": 25.00
                    },
                ],
                "servers": [
                    {
                        "name": "instance-1",
                        "flavor": "lsd.t1.tiny",
                        "hours_used": 744,
                        "status": "Ativo",
                        "cpu_avg": 8.6
                    },
                    {
                        "name": "instance-1",
                        "flavor": "lsd.t1.tiny",
                        "hours_used": 744,
                        "status": "Ativo",
                        "cpu_avg": 8.6
                    },
                    {
                        "name": "instance-1",
                        "flavor": "lsd.t1.tiny",
                        "hours_used": 744,
                        "status": "Ativo",
                        "cpu_avg": 8.6
                    },
                    {
                        "name": "instance-1",
                        "flavor": "lsd.t1.tiny",
                        "hours_used": 744,
                        "status": "Ativo",
                        "cpu_avg": 8.6
                    },
                    {
                        "name": "instance-1",
                        "flavor": "lsd.t1.tiny",
                        "hours_used": 744,
                        "status": "Ativo",
                        "cpu_avg": 8.6
                    }
                ],
                "volumes": [
                    {
                        "name": "volume-1",
                        "size": 10
                    },
                    {
                        "name": "volume-2",
                        "size": 20
                    },
                    {
                        "name": "volume-3",
                        "size": 60
                    },
                    {
                        "name": "volume-4",
                        "size": 80
                    }
                ],
                "flavors": [
                    {
                        "name": "lsd.t1.tiny",
                        "vcpus": 1,
                        "mem_gb": 2048,
                        "disk_size": 40
                    },
                    {
                        "name": "lsd.t1.small",
                        "vcpus": 2,
                        "mem_gb": 4096,
                        "disk_size": 60
                    },
                    {
                        "name": "lsd.t1.medium",
                        "vcpus": 4,
                        "mem_gb": 8192,
                        "disk_size": 80
                    },
                    {
                        "name": "lsd.t1.large",
                        "vcpus": 8,
                        "mem_gb": 16384,
                        "disk_size": 100
                    }               
                ]
            }
        }
    ]
    }
    html_message = render_to_string('user_report_template.html', context)
    plain_message = strip_tags(html_message)
    from_email = 'From Mail'
    to = settings.DEFAULT_FROM_EMAIL
    mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)


def send_mail_plain_text(message, dist):
    subject = 'Subject'
    plain_message = message
    from_email = 'From Mail'
    to = dist
    mail.send_mail(subject, plain_message, from_email, [to])


def send():
    email_subject = "Activate your account"
    email_body = "Email Body"
    email = EmailMessage(
        email_subject,
        email_body,
        'another@example.com',
        [settings.DEFAULT_FROM_EMAIL]
    )
    email.send(fail_silently=False)
