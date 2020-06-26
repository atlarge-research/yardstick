import numpy as np
import pandas as pd
import plotly.graph_objs as go


def to_tick_rate(relative_utilization):
    """Compute the tick rate from the relative utilization."""
    return 20 / max(1.0, relative_utilization)


def summarize(data_frame):
    """"""
    indices = []
    means = []
    errors = []

    users_groups = data_frame.groupby(["players"])
    for users, group in users_groups:

        times = group["relative_utilization"]
        mean = times.mean()
        std = times.std()
        count = times.count()
        # 1.96 is the z-value associated with a confidence interval of 95%.
        error = 1.96 * std / np.sqrt(count)

        indices.append(users)
        means.append(mean)
        errors.append(error)

    return indices, means, errors


def draw_trace(figure, name, indices, means, errors, color, line, marker):
    include_whiskers = errors is not None
    figure.add_trace(go.Scatter(
        name=name,
        x=indices,
        y=means,
        error_y=dict(
            color=color,
            type="data",
            array=errors,
            visible=include_whiskers
        ),
        line={
            "color": color,
            "dash": line
        },
        marker={
            "color": color,
            "symbol": marker,
            "size": 8
        }
    ))


def visualize():

    # Prepare figure
    figure = go.Figure()
    figure.update_layout(
        template="simple_white",
        xaxis_title="Users",
        yaxis_title="Relative Utilization (%)",
        autosize=False,
        width=720,
        height=540
    )
    figure.update_xaxes(
        tickmode="linear",
        tick0=0,
        dtick=25,
        showgrid=True
    )
    figure.update_yaxes(
        showgrid=True
    )

    # Draw traces
    colors = ["#F5793A", "#F5793A", "#A95AA1", "#85C0F9", "#85C0F9"]
    lines = ["solid", "dash", "solid", "solid", "dash"]
    markers = ["square", "square", "diamond", "circle", "circle"]
    index = 0

    data_frame = pd.read_csv("output.csv")
    data_frame = data_frame[data_frame["players"] == data_frame["max_players"]]
    for name, name_data_frame in data_frame.groupby(["name"]):
        indices, means, errors = summarize(name_data_frame)
        draw_trace(figure, name, indices, means, errors, colors[index], lines[index], markers[index])
        index += 1

    # Store figure
    figure.write_html("output.html")


if __name__ == '__main__':
    visualize()
