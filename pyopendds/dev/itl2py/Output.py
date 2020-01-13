from pathlib import Path

from .ast import NodeVisitor


class Output(NodeVisitor):

    def __init__(self, context: dict, path: Path, templates: dict):
        self.context = context
        self.path = path
        self.templates = {}
        for filename, template in templates.items():
            self.templates[path / filename] = context['jinja'].get_template(template)

    def write(self):
        if self.context['dry_run']:
            print('######################################## Create Dir', self.path)
        else:
            self.path.mkdir(exist_ok=True)
        for path, template in self.templates.items():
            content = template.render(self.context)
            if self.context['dry_run']:
                print('======================================== Write file', path)
                print(content)
            else:
                path.write_text(content)
