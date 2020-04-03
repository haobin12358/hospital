from hospital import create_app
from hospital.extensions.register_ext import celery

app = create_app()

if __name__ == '__main__':
    app.run(port=7444)
