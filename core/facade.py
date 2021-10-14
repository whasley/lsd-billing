

# generate report

# send email

# convert email to pdf




from django.shortcuts import render
from django.template.loader import render_to_string

def my_view():
    context = {'some_key': 'some_value'}
    content = render_to_string('template.html', context)
    with open('./sample.html', 'w') as static_file:
        static_file.write(content)
    return render('template.html', context)

my_view()
