from inspect import getmembers, isclass


#from crawlers import freelancer


# def get_subclasses(classes):
#     print([cls.__name__ for cls in classes.__subclasses__()])

def test():
    import src.crawlers
    print src.crawlers
    # module = getattr(src.crawlers, "freelancer")
    print module

test()


# crawlers.crawler_interface = getmembers(module, isclass)
# command = [command for command in crawlers.crawler_interface if command[0] != 'CrawlerInterface']
# print command