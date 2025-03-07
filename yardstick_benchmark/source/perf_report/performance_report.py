from airium import Airium
import datetime

# All the data to go into the report goes here

def get_plots(folder):
    pass

def get_score(metric, experiment):
    pass

def get_experiments():
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
            a.meta(name="viewport", content="width=device-width, initial-scale=1")
            a.link(href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css", rel="stylesheet", integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH", crossorigin="anonymous")
            a.title(_t="Performance Report")

        with a.body():
            a.script(src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js", integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz", crossorigin="anonymous")
            with a.div(klass="container"):
                with a.h1(klass="display-3 text-decoration-underline text-center"):
                    a("Performance Report {}".format(datetime.date.today()))

                with a.h2(klass="display-5 text-decoration-underline"):
                    a("Walk Around")

                with a.div(klass="container"):
                    with a.div(klass="row"):
                        with a.div(klass="col-6 table-responsive"):
                            with a.table(id='table', klass="table table-striped"):
                                with a.thead():
                                    with a.tr():
                                        a.th(scope="col", _t='Metric')
                                        a.th(_t='Graph')
                                        a.th(_t='Score')

                                with a.tbody(klass="table-group-divider"):
                                    with a.tr():
                                        a.td(_t='CPU')
                                        with a.td():
                                            a.img(src="img/cpu_box.png", klass="img-fluid", alt="CPU box plot", style="height: 80%")
                                        a.td(_t='12') 
                                    
                                    with a.tr():
                                        a.td(_t='Tick Duration')
                                        with a.td():
                                            a.img(src="img/tick_duration_box.png", alt="Tick Duration box plot", style="width: 70%")
                                        a.td(_t='12') 

                        with a.div(klass="col"):
                            with a.ul(klass="nav nav-tab", id="graph-tab", role="tablist"):
                                with a.li(klass="nav-item", role="presentation"):
                                    a.button(klass="nav-link active", _t="CPU", id="cpu-tab", **{'data-bs-toggle': 'tab', 'data-bs-target' : "#cpu", 'aria-controls' : 'cpu', 'aria-selected': 'true'}, type="button")
                                with a.li(klass="nav-item", role="presentation"):
                                    a.button(klass="nav-link active", _t="Other", id="other-tab", **{'data-bs-toggle': 'tab', 'data-bs-target' : "#other", 'aria-controls' : 'other', 'aria-selected': 'false'}, type="button")
                    
                        with a.div(klass="tab-content", id="graph-tab-content"):
                            with a.div(klass="tab-pane fade show active", id="cpu", role="tabpanel", **{'aria-labelledby' : 'cpu-tab'}, tabindex="0"):
                                a("This is some test text for the CPU section")
                            with a.div(klass="tab-pane fade show active", id="other", role="tabpanel", **{'aria-labelledby' : 'other-tab'}, tabindex="0"):
                                a("This is other text for testing")
                    
                    with a.div(klass="container"):
                        with a.div(klass="row"):
                            with a.div(klass="col-5"):
                                a.h5(_t="Experiment Details")
                                with a.table(id='table', klass="table table-striped"):
                                    with a.tbody():
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="Workload")
                                            a.td(_t="Walkaround")
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="Duration")
                                            a.td(_t="10 m")
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="Runs")
                                            a.td(_t="1")
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="Environment")
                                            a.td(_t="DAS")
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="Server")
                                            a.td(_t="PaperMC")

                            with a.div(klass="col"):
                                a.h5(_t="Hardware Details")

                                with a.table(id='table', klass="table table-striped"):
                                    with a.tbody():
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="CPU")
                                            a.td(_t="AMD EPYC 7282 16-Core Processor")
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="Memory")
                                            a.td(_t="1 TiB")
                                        with a.tr():
                                            a.td(klass="fw-bold", _t="GPU")
                                            a.td(_t="Something or other")
                                        

                with a.h3(klass="text-decoration-underline text-end text-success"):
                    a("Overall Score: 5")


    html = bytes(a)

    filename = filename + ".html"

    with open(filename, 'wb') as f:
        f.write(bytes(html))

if __name__ == "__main__":
    render_report("test")