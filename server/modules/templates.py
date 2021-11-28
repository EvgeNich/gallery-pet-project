from jinja2 import Environment, FileSystemLoader 

file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
INDEX_TEMPLATE = env.get_template('index.html')
GALLERY_TEMPLATE = env.get_template('gallery.html')
MESSAGE_TEMPLATE = env.get_template('message.html')