from litespeed import start_with_args, App
import src.config as config

if __name__ == '__main__':
    import src.rest.file
    import src.rest.tag

    import src.page_groups.file
    import src.page_groups.static
    import src.page_groups.rest

    start_with_args()
