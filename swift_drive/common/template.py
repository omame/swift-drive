# def get_template(template_name, info):
#     template = template_dir + '/%s.tmpl' % template_name

#     try:
#         f = open(template, 'r')
#         file = f.read()
#         f.close()
#         message = file % {'SYSTEM': host, 'ERROR': results.get('message')}
#     except:
#         raise
