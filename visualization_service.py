from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns


CHART_PATH = Path(__file__).with_name("admin_analytics.png")


def create_admin_visualization(analytics, show=True):
    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(1, 2, figsize=(11, 5))
    figure.suptitle(
        f"Mini Store Sales | {analytics['order_count']} orders | "
        f"${analytics['revenue']:,.2f} revenue",
        fontsize=14,
        fontweight="bold",
    )

    products = [
        dict(product)
        for product in analytics["products"]
        if product["units_sold"] > 0
    ]
    if not products:
        axes[0].text(0.5, 0.5, "No product sales yet", ha="center", va="center")
        axes[0].set_axis_off()
    else:
        sns.barplot(
            x=[product["units_sold"] for product in products],
            y=[product["name"] for product in products],
            color="#2a9d8f",
            ax=axes[0],
        )
        axes[0].bar_label(axes[0].containers[0], padding=3)
        axes[0].set_title("Products sold")
        axes[0].set_xlabel("Units sold")
        axes[0].set_ylabel("")

    cities = [dict(city) for city in analytics["cities"]]
    if not cities:
        axes[1].text(0.5, 0.5, "No shipments yet", ha="center", va="center")
        axes[1].set_axis_off()
    else:
        sns.barplot(
            x=[city["order_count"] for city in cities],
            y=[city["city"] for city in cities],
            color="#457b9d",
            ax=axes[1],
        )
        axes[1].bar_label(axes[1].containers[0], padding=3)
        axes[1].set_title("Orders by city")
        axes[1].set_xlabel("Orders")
        axes[1].set_ylabel("")

    figure.tight_layout()
    figure.savefig(CHART_PATH, dpi=160, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(figure)
    return CHART_PATH