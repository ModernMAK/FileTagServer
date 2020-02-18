from io import open
from os.path import dirname, join
from webserver.server import route, start_with_args

if __name__ == '__main__':
    @route()
    def index(request):
        desired_file = "html/example.html"
        current_directory = dirname(__file__)
        desired_path = desired_file#join(current_directory, desired_file)

        with open(desired_path) as file:
            return file.read()
#        return [b'Not Implemented']



    @route("/stylesheets/(\w*).css*")
    def stylesheets(request,sheet_requested):
        with open(f"stylesheets/{sheet_requested}.css") as file:
            return file.read()



    start_with_args()