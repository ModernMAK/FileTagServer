from litespeed import start_with_args, route, serve
from os.path import join
from os import getcwd


@route('/')
def index(request):
    print('a')
    return media(request, 'index.html')


@route(r'/(.*)', no_end_slash=True)
def media(request, file):
    print('b')
    file_path = getcwd() + '/' + join('quicktest', file)
    print(file_path)
    return serve(file_path)


if __name__ == '__main__':
    start_with_args()
