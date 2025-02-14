from airium import Airium
import datetime

# All the data to go into the report goes here

def get_plots(folder):
    pass

def get_score(metric, experiment):
    pass

# CPU data + graphs
# Tick Duration + graphs

#Report rendering goes here
def render_report(filename):
        
    a = Airium()

    a('<!DOCTYPE html>')
    with a.html(lang="pl"):
        with a.head():
            a.meta(charset="utf-8")
            a.title(_t="Performance Report")

        with a.body():
            with a.h1(id="main", klass='main_header'):
                a("Performance Report {}".format(datetime.date.today()))

            with a.h2(id="Experiment 1", klass='experiment_header'):
                a("Experiment 1")

            with a.table(id='table'):
                with a.tr(klass='header_row'):
                    a.th(_t='Metric')
                    a.th(_t='Graph')
                    a.th(_t='Score')

                with a.tr():
                    a.td(_t='CPU')
                    a.td(id='jbl', _t='----__-')
                    a.td(_t='12') 
                
                with a.tr():
                    a.td(_t='Tick Duration')
                    a.td(id='jbl', _t='__^--')
                    a.td(_t='12') 

    html = bytes(a)

    filename = filename + ".html"

    with open(filename, 'wb') as f:
        f.write(bytes(html))

if __name__ == "__main__":
    render_report("test")