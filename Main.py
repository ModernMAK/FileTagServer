from io import open
from os.path import dirname, join
from webserver.server import route, start_with_args, serve
from pystache import Renderer

if __name__ == '__main__':
    renderer = Renderer()


    @route()
    def index(request):
        return serve("html/upload.html")

        # desired_file = "html/example.html"
        desired_file = "html/testpost.html"
        content, status, header = serve(desired_file)
        fixed_content = renderer.render(content, {'TITLE': "Title", 'IMG_ALT': "Misdreavous", 'IMG_HEIGHT': 330,
                                                  'IMG_WIDTH': 360, 'IMG_PATH': "misdreavus.jpg"})
        return fixed_content, status, header


    @route("stylesheets/(.*)")
    def stylesheets(request, file):
        return serve(f"stylesheets/{file}")


    @route("images/dynamic/(.*)")
    def dynamic_images(request, file):
        return serve(f"images/dynamic/{file}")


    @route("images/static/(.*)")
    def dynamic_images(request, file):
        return serve(f"images/static/{file}")


    @route("upload/img", methods=['POST'])
    def dynamic_images(request):
        img = request['POST']

        pass


    start_with_args()
